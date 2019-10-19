from .TabStackedWidget import TabStackedWidget
from .TabBar import TabBar
from mc.common import const
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QToolButton
from PyQt5.Qt import Qt
from mc.common.globalvars import gVar
from mc.tools.ToolButton import ToolButton
from PyQt5.Qt import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QClipboard
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.app.Settings import Settings
from PyQt5.Qt import QIcon
from mc.webtab.WebTab import WebTab
from mc.webengine.LoadRequest import LoadRequest
from mc.tools.ClosedTabsManager import ClosedTabsManager
from PyQt5.Qt import QAction

class AddTabButton(ToolButton):
    def __init__(self, tabWidget, tabBar):
        super(AddTabButton, self).__init__(tabBar)
        self._tabBar = tabBar  # TabBar
        self._tabWidget = tabWidget  # TabWidget
        self.setObjectName('tabwidget-button-addtab')
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAcceptDrops(True)
        self.setToolTip('New Tab')

    # private:
    # override
    def wheelEvent(self, event):
        '''
        @param: event QWheelEvent
        '''
        self._tabBar.wheelEvent(event)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if event.button() == Qt.MiddleButton and self.rect().contains(event.pos()):
            self._tabWidget.addTabFromClipboard()
        super(AddTabButton, self).mouseReleaseEvent(event)

class MenuTabs(QMenu):
    # Q_SIGNALS
    closeTab = pyqtSignal(int)

    # private
    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if event.button() == Qt.MiddleButton:
            action = self.actionAt(event.pos())
            if action and action.isEnabled():
                # TODO: qobject_cast<WebTab*>(qvariant_cast<QWidget*>)
                tab = action.data()
                if tab:
                    self.closeTab.emit(tab.tabIndex())
                    action.setEnable(False)
                    event.accept()
        super(MenuTabs, self).mouseReleaseEvent(event)

class TabWidget(TabStackedWidget):
    def __init__(self, window, parent=None):
        super(TabWidget, self).__init__(parent)

        self._window = None  # BrowserWindow
        self._tabBar = None  # TabBar
        self._locationBars = None  # QStackedWidget
        self._closedTabsManager = None  # ClosedTabsManager

        self._menuTabs = None  # MenuTabs
        self._buttonListTabs = None  # ToolButton
        self._menuClosedTabs = None  # QMenu
        self._buttonClosedTabs = None  # ToolButton
        self._buttonAddTab = None  # AddTabButton
        self._buttonAddTab2 = None  # AddTabButton

        self._lastBackgroundTab = None  # QPoint<WebTab>

        self._dontCloseWithOneTab = False
        self._showClosedTabsButton = False
        self._newTabAfterActive = False
        self._newEmptyTabAfterActive = False
        self._urlOnNewTab = QUrl()  # QUrl

        self._currentTabFresh = False
        self._blockTabMovedSignal = False

        # start init
        self._window = window
        self._locationBars = QStackedWidget()
        self._closedTabsManager = ClosedTabsManager()

        self.setObjectName('tabWidget')
        self._tabBar = TabBar(self._window, self)
        self.setTabBar(self._tabBar)

        self.changed.connect(gVar.app.changeOccurred)
        self.pinStateChanged.connect(self.changed)

        self._tabBar.tabCloseRequested.connect(self.requestCloseTab)
        self._tabBar.tabMoved.connect(self._tabWasMoved)

        self._tabBar.moveAddTabButton.connect(self.moveAddTabButton)
        gVar.app.settingsReloaded.connect(self._loadSettings)

        self._menuTabs = MenuTabs(self)
        self._menuTabs.closeTab.connect(self.requestCloseTab)

        self._menuClosedTabs = QMenu(self)

        # AddTab button displayed next to last tab
        self._buttonAddTab = AddTabButton(self, self._tabBar)
        self._buttonAddTab.setProperty('outside-tabbar', False)
        self._buttonAddTab.clicked.connect(self._window.addTab)

        # AddTab button displayed ouside tabbar (as corner widget)
        self._buttonAddTab2 = AddTabButton(self, self._tabBar)
        self._buttonAddTab2.setProperty('outside-tabbar', True)
        self._buttonAddTab2.hide()
        self._buttonAddTab2.clicked.connect(self._window.addTab)

        # ClosedTabs button displayed as a permanet corner widget
        self._buttonClosedTabs = ToolButton(self._tabBar)
        self._buttonClosedTabs.setObjectName('tabwidget-button-closedtabs')
        self._buttonClosedTabs.setMenu(self._menuClosedTabs)
        self._buttonClosedTabs.setPopupMode(QToolButton.InstantPopup)
        self._buttonClosedTabs.setToolTip('Closed tabs')
        self._buttonClosedTabs.setAutoRaise(True)
        self._buttonClosedTabs.setFocusPolicy(Qt.NoFocus)
        self._buttonClosedTabs.setShowMenuInside(True)
        self._buttonClosedTabs.aboutToShowMenu.connect(self._aboutToShowClosedTabsMenu)

        # ListTabs button is showed only when tabbar overflows
        self._buttonListTabs = ToolButton(self._tabBar)
        self._buttonListTabs.setObjectName('tabwidget-button-opentabs')
        self._buttonListTabs.setMenu(self._menuTabs)
        self._buttonListTabs.setPopupMode(QToolButton.InstantPopup)
        self._buttonListTabs.setToolTip('List of tabs')
        self._buttonListTabs.setAutoRaise(True)
        self._buttonListTabs.setFocusPolicy(Qt.NoFocus)
        self._buttonListTabs.setShowMenuInside(True)
        self._buttonListTabs.hide()
        self._buttonListTabs.aboutToShowMenu.connect(self._aboutToShowTabsMenu)

        self._tabBar.addCornerWidget(self._buttonAddTab2, Qt.TopRightCorner)
        self._tabBar.addCornerWidget(self._buttonClosedTabs, Qt.TopRightCorner)
        self._tabBar.addCornerWidget(self._buttonListTabs, Qt.TopRightCorner)
        self._tabBar.overFlowChanged.connect(self.tabBarOverFlowChanged)

        self._loadSettings()

    def browserWindow(self):
        return self._window

    def restoreState(self, tabs, currentTab):
        '''
        @param: tabs QVector<WebTab::SavedTab>
        '''
        if not tabs:
            return False

        childTabs = []  # QVector<QPair<WebTab*, QVector<int>>>

        for tab in tabs:
            index = self.addViewByUrl(QUrl(), const.NT_CleanSelectedTab,
                False, tab.isPinned)
            webTab = self._weTab(index)
            webTab.restoreTab(tab)
            if tab.childTabs:
                childTabs.append([webTab, tab.childTabs])

        for webTab, tabs in childTabs:
            for index in tabs:
                t = self._weTab(index)
                if t:
                    webTab.addChildTab(t)

        self.setCurrentIndex(currentTab)
        QTimer.singleShot(0, self._tabBar.ensureVisible)

        self._weTab().tabActivated()

        return True

    def setCurrentIndex(self, index):
        super(TabWidget, self).setCurrentIndex(index)

    def nextTab(self):
        index = (self.currentIndex() + 1) % self.count()
        self.setCurrentIndex(index)

    def previousTab(self):
        if self.currentIndex() == 0:
            index = self.count() - 1
        else:
            index = self.currentIndex() - 1
        self.setCurrentIndex(index)

    def currentTabChanged(self, index):
        if not self._validIndex(index):
            return

        self._lastBackgroundTab = None
        self._currentTabFresh = False

        webTab = self._weTab(index)
        webTab.tabActivated()

        locBar = webTab.locationBar()

        if locBar and self._locationBars.indexOf(locBar) != -1:
            self._locationBars.setCurrentWidget(locBar)

        self._window.currentTabChanged()

        self.changed.emit()

    def normalTabsCount(self):
        return self._tabBar.normalTabsCount()

    def pinnedTabsCount(self):
        return self._tabBar.pinnedTabsCount()

    def extraReservedWidth(self):
        return self._buttonAddTab.width()

    def webTab(self, index=-1):
        '''
        @return: WebTab
        '''
        if index < 0:
            return self._weTab()
        else:
            return self._weTab(index)

    def tabBar(self):
        '''
        @return: TabBar
        '''
        return self._tabBar

    def closedTabsManager(self):
        '''
        @return: ClosedTabsManager
        '''
        return self._closedTabsManager

    def allTabs(self, withPinned=True):
        '''
        @return: QList<WebTab*>
        '''
        allTabs = []

        for idx in range(self.count()):
            tab = self._weTab(idx)
            if not tab or (not withPinned and tab.isPinned()):
                continue
            allTabs.append(tab)

        return allTabs

    def canRestoreTab(self):
        return self._closedTabsManager.isClosedTabAvailable()

    def isCurrentTabFresh(self):
        return self._currentTabFresh

    def setCurrentTabFresh(self, currentTabFresh):
        self._currentTabFresh = currentTabFresh

    def locationBars(self):
        '''
        @return: QStackedWidget
        '''
        return self._locationBars

    def buttonClosedTabs(self):
        '''
        @return: ToolButton
        '''
        return self._buttonClosedTabs

    def buttonAddTab(self):
        '''
        @return: AddTabButton
        '''
        return self._buttonAddTab

    def moveTab(self, from_, to_):
        if not self._validIndex(to_) or from_ == to_:
            return
        tab = self.webTab(from_)
        if not tab:
            return
        self._blockTabMovedSignal = True
        # (Un)pin tab when needed
        if (tab.isPinned() and to_ >= self.pinnedTabsCount()) or \
                (not tab.isPinned() and to_ < self.pinnedTabsCount()):
            tab.togglePinned()
        super(TabWidget, self).moveTab(from_, to_)
        self._blockTabMovedSignal = False
        self.tabMoved.emit(from_, to_)

    def pinUnPinTab(self, index, title=''):
        newIndex = super(TabWidget, self).pinUnPinTab(index, title)
        if index != newIndex and not self._blockTabMovedSignal:
            self.tabMoved.emit(index, newIndex)
        return newIndex

    def detachTab(self, tab):
        '''
        @param: tab WebTab
        '''
        assert(tab)

        if self.count() == 1 and gVar.app.windowCount() == 1:
            return

        self._locationBars.removeWidget(tab.locationBar())
        tab.webView().wantsCloseTab.disconnect(self.closeTab)
        tab.webView().urlChanged.disconnect(self.changed)
        tab.webView().ipChanged.disconnect(self._window.ipLabel().setText)

        index = tab.tabIndex()

        tab.detach()
        tab.setPinned(False)

        self.tabRemoved.emit(index)

        if self.count() == 0:
            self._window.close()

    def addViewByUrl(self, url, openFlags, selectLine=False, pinned=False):
        return self.addViewByReq(LoadRequest(url), openFlags, selectLine, pinned)

    # Q_SLOTS:
    def addViewByReq(self, req, openFlags, selectLine=False, pinned=False):
        '''
        @param: req LoadRequest
        @param: openFlags Qz::NewTabPositionFlags
        @param: selectLine bool
        @param: pinned bool
        '''
        assert(isinstance(req, LoadRequest))
        return self.addViewByReqTitle(req, '', openFlags, selectLine, -1, pinned)


    def addViewByUrlTitle(self, url, title="New tab", openFlags=const.NT_SelectedTab,  # noqa C901
            selectLine=False, position=-1, pinned=False):
        return self.addViewByReqTitle(LoadRequest(url), title, openFlags,
                selectLine, position, pinned)

    def addViewByReqTitle(self, req, title="New tab", openFlags=const.NT_SelectedTab,  # noqa C901
            selectLine=False, position=-1, pinned=False):
        '''
        @param: req LoadRequest
        @param: title QString
        @param: openFlags Qz::NewTabPositionFlags
        @param: selectLine bool
        @param: position int
        @param: pinned bool
        '''
        if isinstance(req, QUrl):
            req = LoadRequest(req)
        url = req.url()
        self._currentTabFresh = False

        if url.isEmpty() and not (openFlags & const.NT_CleanTab):
            url = self._urlOnNewTab

        openAfterActive = self._newTabAfterActive and not (openFlags & const.NT_TabAtTheEnd)

        if openFlags == const.NT_SelectedNewEmptyTab and self._newEmptyTabAfterActive:
            openAfterActive = True

        if openAfterActive and position == -1:
            # If we are opening newBgTab from pinned tab, make sure it won't be
            # openned between other pinned tabs
            if openFlags & const.NT_NotSelectedTab and self._lastBackgroundTab:
                position = self._lastBackgroundTab.tabIndex() + 1
            else:
                position = max(self.currentIndex() + 1, self._tabBar.pinnedTabsCount())

        webTab = WebTab(self._window)
        webTab.setPinned(pinned)
        webTab.locationBar().showUrl(url)
        self._locationBars.addWidget(webTab.locationBar())

        if position == -1:
            insertIndex = self.count()
        else:
            insertIndex = position
        index = self.insertTab(insertIndex, webTab, '', pinned)
        webTab.attach(self._window)

        if title:
            self._tabBar.setTabText(index, title)

        if openFlags & const.NT_SelectedTab:
            self.setCurrentIndex(index)
        else:
            self._lastBackgroundTab = webTab

        webTab.webView().wantsCloseTab.connect(self.closeTab)
        webTab.webView().urlChanged.connect(self.changed)
        webTab.webView().ipChanged.connect(self._window.ipLabel().setText)

        def urlChangedCb(url):
            if url != self._urlOnNewTab:
                self._currentTabFresh = False
        webTab.webView().urlChanged.connect(urlChangedCb)

        if url.isValid() and url != req.url():
            r = LoadRequest(req)
            r.setUrl(url)
            webTab.webView().loadByReq(r)
        elif req.url().isValid():
            webTab.webView().loadByReq(req)

        if selectLine and not self._window.locationBar().text():
            self._window.locationBar().setFocus()

        # Make sure user notice opening new background tabs
        if not (openFlags & const.NT_SelectedTab):
            self._tabBar.ensureVisible(index)

        self.changed.emit()
        self.tabInserted.emit(index)

        return index

    def addViewByTab(self, tab, openFlags):
        '''
        @param: tab WebTab
        @param: openFlags Qz::NewTabPositionFlags
        '''
        return self.insertView(self.count() + 1, tab, openFlags)

    def insertView(self, index, tab, openFlags):
        '''
        @param: index int
        @param: tab WebTab
        @param: openFlags Qz::NewTabPositionFlags
        '''
        self._locationBars.addWidget(tab.locationBar())
        newIndex = self.insertTab(index, tab, '', tab.isPinned())
        tab.attach(self._window)

        if openFlags & const.NT_SelectedTab:
            self.setCurrentIndex(newIndex)
        else:
            self._lastBackgroundTab = tab

        tab.webView().wantsCloseTab.connect(self.closeTab)
        tab.webView().urlChanged.connect(self.changed)
        tab.webView().ipChanged.connect(self._window.ipLabel().setText)

        # Make sure user notice opening new background tabs
        if not (openFlags & const.NT_SelectedTab):
            self._tabBar.ensureVisible(index)

        self.changed.emit()
        self.tabInserted.emit(newIndex)

        return newIndex

    def addTabFromClipboard(self):
        # QString
        selectionClipboard = QApplication.clipboard().text(QClipboard.Selection)
        # QUrl
        guessedUrl = QUrl.fromUserInput(selectionClipboard)

        if not guessedUrl.isEmpty():
            self.addViewByUrl(guessedUrl, const.NT_SelectedNewEmptyTab)

    def duplicateTab(self, index):
        if not self._validIndex(index):
            return

        webTab = self._weTab(index)

        index = self.addViewByUrlTitle(QUrl(), webTab.title(), const.NT_CleanSelectedTab)
        newWebTab = self._weTab(index)
        newWebTab.p_restoreTabByUrl(webTab.url(), webTab.historyData(), webTab.zoomLevel())

        return index

    def closeTab(self, index=-1):
        '''
        @brief: Force close tab
        '''
        if index == -1:
            index = self.currentIndex()

        webTab = self._weTab(index)
        if not webTab or not self._validIndex(index):
            return

        # This is already handled in requestClosetab
        if self.count() <= 1:
            self.requestCloseTab(index)
            return

        self._closedTabsManager.saveTab(webTab)

        webView = webTab.webView()
        self._locationBars.removeWidget(webView.webTab().locationBar())
        webView.wantsCloseTab.disconnect(self.closeTab)
        webView.urlChanged.disconnect(self.changed)
        webView.ipChanged.disconnect(self._window.ipLabel().setText)

        self._lastBackgroundTab = None

        webTab.detach()
        webTab.deleteLater()

        self._updateClosedTabsButton()

        self.changed.emit()
        self.tabRemoved.emit(index)

    def requestCloseTab(self, index=-1):
        '''
        @brief: Request close tab (may be rejected)
        '''
        if index == -1:
            index = self.currentIndex()

        webTab = self._weTab(index)
        if not webTab or not self._validIndex(index):
            return

        webView = webTab.webView()

        # This would close last tab, so we close the window instead
        if self.count() <= 1:
            # If we are not closing window upon closing last tab, let's just
            # load new-tab-url
            if self._dontCloseWithOneTab:
                # We don't want to accumulate more than one closed tab, if user
                # tries to close the last tab multiple times
                if webView.url() != self._urlOnNewTab:
                    self._closedTabsManager.saveTab(webTab)
                webView.zoomReset()
                webView.load(self._urlOnNewTab)
                return
            self._window.close()
            return

        webView.triggerPageAction(QWebEnginePage.RequestClose)

    def reloadTab(self, index):
        if not self._validIndex(index):
            return

        self._weTab(index).reload()

    def reloadAllTabs(self):
        for idx in range(self.count()):
            self.reloadTab(idx)

    def stopTab(self, index):
        if not self._validIndex(index):
            return

        self._weTab(index).stop()

    def closeAllButCurrent(self, index):
        if not self._validIndex(index):
            return

        akt = self._weTab(index)
        tabs = self.allTabs(False)
        for tab in tabs:
            tabIndex = tab.tabIndex()
            if akt == self.widget(tabIndex):
                continue
            self.requestCloseTab(tabIndex)

    def closeToRight(self, index):
        if not self._validIndex(index):
            return

        tabs = self.allTabs(False)
        for tab in tabs:
            tabIndex = tab.tabIndex()
            if index >= tabIndex:
                continue
            self.requestCloseTab(tabIndex)

    def closeToLeft(self, index):
        if not self._validIndex(index):
            return

        tabs = self.allTabs(False)
        for tab in tabs:
            tabIndex = tab.tabIndex()
            if index <= tabIndex:
                continue
            self.requestCloseTab(tabIndex)

    # NOTICE: detachTab renamed to detachTabByIndex
    def detachTabByIndex(self, index):
        tab = self._weTab(index)
        assert(tab)

        if self.count() == 1 and gVar.app.windowCount() == 1:
            return

        self.detachTab(tab)

        # BrowserWindow* window
        window = gVar.app.createWindow(const.BW_NewWindow)
        window.setStartTab(tab)

    def loadTab(self, index):
        if not self._validIndex(index):
            return

        self._weTab(index).tabActivated()

    def unloadTab(self, index):
        if not self._validIndex(index):
            return

        self._weTab(index).unload()

    def restoreClosedTab(self, obj=0):
        '''
        @param: obj QObject
        '''
        if not obj:
            obj = self.sender()

        if not self._closedTabsManager.isClosedTabAvailable():
            return

        tab = ClosedTabsManager.Tab()

        action = obj
        if isinstance(action, QAction) and action.data().toInt() != 0:
            tab = self._closedTabsManager.takeTabAt(action.data().toInt())
        else:
            tab = self._closedTabsManager.takeLastClosedTab()

        if tab.position < 0:
            return

        index = self.addViewByUrl(QUrl(), tab.tabState.title, const.NT_CleanSelectedTab, False, tab.position)
        webTab = self._weTab(index)
        webTab.setParentTab(tab.parentTab)
        webTab.p_restoreTab(tab.tabState)

        self._updateClosedTabsButton()

    def restoreAllClosedTabs(self):
        if not self._closedTabsManager.isClosedTabAvailable():
            return

        closedTabs = self._closedTabsManager.closedTabs()
        for tab in closedTabs:
            index = self.addViewByUrl(QUrl(), tab.tabState.title, const.NT_CleanSelectedTab)
            webTab = self._weTab(index)
            webTab.setParentTab(tab.parentTab)
            webTab.p_restoreTab(tab.tabState)

        self.clearClosedTabsList()

    def clearClosedTabsList(self):
        self._closedTabsManager.clearClosedTabs()
        self._updateClosedTabsButton()

    def moveAddTabButton(self, posX):
        posY = (self._tabBar.height() - self._buttonAddTab.height()) / 2

        if QApplication.layoutDirection() == Qt.RightToLeft:
            posX = max(posX - self._buttonAddTab.width(), 0)
        else:
            posX = min(posX, self._tabBar.width() - self._buttonAddTab.width())

        self._buttonAddTab.move(posX, posY)

    def tabBarOverFlowChanged(self, overflowed):
        # Show buttons inside tabbar
        self._buttonAddTab.setVisible(not overflowed)

        # Show buttons displayed outside tabbar (corner widgets)
        self._buttonAddTab2.setVisible(overflowed)
        self._buttonListTabs.setVisible(overflowed)

    # Q_SIGNALS:
    changed = pyqtSignal()
    tabInserted = pyqtSignal(int)  # index
    tabRemoved = pyqtSignal(int)  # index
    tabMoved = pyqtSignal(int, int)  # from ,to

    # private Q_SLOTS:
    def _loadSettings(self):
        settings = Settings()
        settings.beginGroup('Browser-Tabs-Settings')
        self._dontCloseWithOneTab = settings.value('dontCloseWithOneTab', False, type=bool)
        self._showClosedTabsButton = settings.value('showClosedTabsButton', False, type=bool)
        self._newTabAfterActive = settings.value('newTabAfterActive', True, type=bool)
        self._newEmptyTabAfterActive = settings.value('newEmptyTabAfterActive', False, type=bool)
        settings.endGroup()

        settings.beginGroup('Web-URL-Settings')
        self._urlOnNewTab = settings.value('newTabUrl', 'app:speeddial', type=QUrl)
        settings.endGroup()

        self._tabBar.loadSettings()

        self._updateClosedTabsButton()

    def _aboutToShowTabsMenu(self):
        self._menuTabs.clear()

        for idx in range(self.count()):
            tab = self._weTab(idx)
            if not tab or tab.isPinned():
                continue

            action = QAction(self)
            action.setIcon(tab.icon())

            if idx == self.currentIndex():
                f = action.font()
                f.setBold(True)
                action.setFont(f)

            title = tab.title()
            title.replace('&', '&&')
            action.setText(gVar.appTools.truncatedText(title, 40))

            # TODO: QVariant::fromValue(qobject_cast<QWidget*>(tab)
            action.setData(tab)
            action.triggered.connect(self._actionChangeIndex)
            self._menuTabs.addAction(action)

    def _aboutToShowClosedTabsMenu(self):
        self._menuClosedTabs.clear()

        closedTabs = self.closedTabsManager().closedTabs()
        for idx, tab in enumerate(closedTabs):
            title = gVar.appTools.truncatedText(tab.tabState.title, 40)
            self._menuClosedTabs.addAction(
                tab.tabState.icon, title, self.restoreClosedTab
            ).setData(idx)

        if self._menuClosedTabs.isEmpty():
            self._menuClosedTabs.addAction('Empty').setEnabled(False)
        else:
            self._menuClosedTabs.addSeparator()
            self._menuClosedTabs.addAction('Restore All Closed Tabs',
                self.restoreAllClosedTabs)
            self._menuClosedTabs.addAction(QIcon.fromTheme('edit-clear'),
                'Clear list', self.clearClosedTabsList)

    def _actionChangeIndex(self):
        # TODO: QAction* action = qobject_cast<QAction*>(sender())
        action = self.sender()
        if action:
            # TODO: qobject_cast<WebTab*>(qvariant_cast<QWidget*>(action.data()))
            tab = action.data()
            if tab:
                self._tabBar.ensureVisible(tab.tabIndex())
                self.setCurrentIndex(tab.tabIndex())

    def _tabWasMoved(self, before, after):
        '''
        @param: before int
        @param: after int
        '''
        self._lastBackgroundTab = None

        self.changed.emit()
        if not self._blockTabMovedSignal:
            self.tabMoved.emit(before, after)

    # private:
    def _weTab(self, index=None):
        '''
        @return: WebTab
        '''
        if index is None:
            index = self.currentIndex()
        result = self.widget(index)
        if isinstance(result, WebTab):
            return result
        else:
            return None

    def _tabIcon(self, index):
        '''
        @return: TabIcon
        '''
        self._weTab(index).tabIcon()

    def _validIndex(self, index):
        return index >= 0 and index < self.count()

    def _updateClosedTabsButton(self):
        self._buttonClosedTabs.setVisible(self._showClosedTabsButton and self.canRestoreTab())

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        #if gVar.app.plugins().processKeyPress(const.ON_TabWidget, self, event):
        #    return
        super(TabWidget, self).keyPressEvent(event)

    # override
    def keyReleaseEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        #if gVar.app.plugins().processKeyRelease(const.ON_TabWidget, self, event):
        #    return
        super(TabWidget, self).keyReleaseEvent(event)
