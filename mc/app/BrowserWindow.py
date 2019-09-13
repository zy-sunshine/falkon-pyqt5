from PyQt5.QtWidgets import QMainWindow
from mc.sidebar.SideBar import SideBarManager
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QUrl
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QTextCodec
from PyQt5.Qt import Qt
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QEvent
from PyQt5.Qt import QMessageBox
from PyQt5.Qt import QTimer
from PyQt5.Qt import QVBoxLayout
from PyQt5.QtWidgets import QSplitter
from PyQt5.Qt import QRect
from PyQt5.Qt import QMenu
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QShortcut
from PyQt5.QtWidgets import QLabel
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QMenuBar
from PyQt5.Qt import QAction, QActionGroup

from mc.webengine.LoadRequest import LoadRequest
from mc.common import const
from .Settings import Settings
from mc.common.globalvars import gVar
from mc.sidebar.SideBar import SideBar
from mc.bookmarks.BookmarksTools import BookmarksTools
from mc.tabwidget.TabWidget import TabWidget
from mc.other.CheckBoxDialog import CheckBoxDialog

from mc.navigation.NavigationBar import NavigationBar
from mc.bookmarks.BookmarksToolbar import BookmarksToolbar
from mc.tabwidget.TabModel import TabModel
from mc.tabwidget.TabMruModel import TabMruModel
from mc.other.StatusBar import StatusBar
from mc.tools.ProgressBar import ProgressBar
from mc.navigation.NavigationContainer import NavigationContainer
from mc.downloads.DownloadsButton import DownloadsButton
from mc.tools.MenuBar import MenuBar
from mc.app.MainMenu import MainMenu
from mc.navigation.LocationBar import LocationBar

class BrowserWindow(QMainWindow):
    class SavedWindow(object):
        def __init__(self, window=None):
            '''
            @param: window BrowserWindow
            '''
            self.init(window)

        def init(self, window):
            if window:
                pass
            else:
                self.windowState = QByteArray()
                self.windowGeometry = QByteArray()
                self.windowUiState = {}  # QString -> QVariant
                self.virtualDesktop = -1
                self.currentTab = -1
                self.tabs = []  # WebTab.SavedTab

        def isValid(self):
            for tab in self.tabs:
                if not tab.isValid():
                    return False
            return self.currentTab > -1

        def clear(self):
            self.windowState.clear()
            self.windowGeometry.clear()
            self.virtualDesktop = -1
            self.currentTab = -1
            self.tabs.clear()

    def __init__(self, type_, startUrl=QUrl()):
        super().__init__(None)
        self._startUrl = startUrl
        self._homepage = QUrl()
        self._windowType = type_
        self._startTab = None  # WebTab
        self._startPage = None  # WebPage
        self._mainLayout = None  # QVBoxLayout
        self._mainSplitter = None  # QSplitter
        self._tabWidget = None  # TabWidget
        self._sideBar = None  # QPointer<SideBar>
        self._sideBarManager = SideBarManager(self)
        self._statusBar = None

        self._navigationContainer = None  # NavigationContainer
        self._navigationToolbar = None  # NavigationBar
        self._bookmarksToolbar = None  # BookmarksToolbar

        self._progressBar = None  # ProgressBar
        self._ipLabel = None  # QLabel
        self._superMenu = None  # QMenu
        self._mainMenu = None  # MainMenu

        self._tabModel = None  # TabModel
        self._tabMruModel = None  # TabMruModel

        self._sideBarWidth = 0
        self._webViewWidth = 0

        # Shortcuts
        self._useTabNumberShortcuts = False
        self._useSpeedDialNumberShortcuts = False
        self._useSingleKeyShortcuts = False

        # Remember visibility of menubar and statusbar after entering Fullscreen
        self._menuBarVisible = False
        self._statusBarVisible = False
        self._htmlFullScreenView = None  # TabbedWebView
        self._hideNavigationTimer = None  # QTimer

        self._deleteOnCloseWidgets = []  # QList<QPointer<QWidget>>

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)

        self.setObjectName('mainwindow')
        self.setWindowTitle(const.APPNAME)
        self.setProperty('private', gVar.app.isPrivate())

        self._setupUi()
        self._setupMenu()

        self._hideNavigationTimer = QTimer(self)
        self._hideNavigationTimer.setInterval(1000)
        self._hideNavigationTimer.setSingleShot(True)
        self._hideNavigationTimer.timeout.connect(self._hideNavigationSlot)

        gVar.app.settingsReloaded.connect(self._loadSettings)

        QTimer.singleShot(0, self._postLaunch)

        if gVar.app.isPrivate():
            gVar.appTools.setWmClass('%s Browser (Private Window)' % const.APPNAME, self)
        else:
            gVar.appTools.setWmClass('%s Browser' % const.APPNAME, self)

    def __del__(self):
        gVar.app.plugins().emitMainWindowDeleted(self)
        for widget in self._deleteOnCloseWidgets:
            widget.deleteLater()

    def setStartTab(self, tab):
        '''
        @param: tab WebTab
        '''
        self._startTab = tab

    def setStartPage(self, page):
        '''
        @param: page WebPage
        '''
        self._startPage = page

    def restoreWindow(self, window):
        '''
        @param: window SavedWindow
        '''
        self.restoreState(window.windowState)
        self.restoreGeometry(window.windowGeometry)
        self._restoreUiState(window.windowUiState)
        if not self.gVar.app.isTestModeEnabled():
            self.show()  # Window has to be visible before adding QWebEngineView's
        self._tabWidget.restoreState(window.tabs, window.currentTab)
        self._updateStartupFocus()

    def fullScreenNavigationVisible(self):
        return self._navigationContainer.isVisible()

    def showNavigationWithFullScreen(self):
        if self._htmlFullScreenView:
            return
        if self._hideNavigationTimer.isActive():
            self._hideNavigationTimer.stop()
        self._navigationContainer.show()

    def hideNavigationWithFullScreen(self):
        if self._tabWidget.isCurrentTabFresh():
            return
        if not self._hideNavigationTimer.isActive():
            self._hideNavigationTimer.start()

    def currentTabChanged(self):
        view = self.weView()
        self._navigationToolbar.setCurrentView(view)
        if not view:
            return

        title = view.webTab().title(True)  # allowEmpty
        if not title:
            self.setWindowTitle(const.APPNAME)
        else:
            self.setWindowTitle('%s - %s' % (title, const.APPNAME))
        self._ipLabel.setText(view.getIp())
        view.setFocus()

        self.updateLoadingActions()

        # Settings correct tab order (LocationBar -> WebSearchBar -> WebView)
        self.setTabOrder(self.locationBar(), self._navigationToolbar.webSearchBar())
        self.setTabOrder(self._navigationToolbar.webSearchBar(), view)

    def updateLoadingActions(self):
        view = self.weView()
        if not view:
            return

        isLoading = view.isLoading()
        self._ipLabel.setVisible(not isLoading)
        self._progressBar.setVisible(isLoading)
        self.action('View/Stop').setEnabled(isLoading)
        self.action('View/Reload').setEnabled(not isLoading)

        if isLoading:
            self._progressBar.setValue(view.loadingProgress())
            self._navigationToolbar.showStopButton()
        else:
            self._navigationToolbar.showReloadButton()

    def addBookmark(self, url, title):
        BookmarksTools.addBookmarkDilaog(self, url, title)

    def addDeleteOnCloseWidget(self, widget):
        '''
        @param: widget QWidget
        '''
        if widget not in self._deleteOnCloseWidgets:
            self._deleteOnCloseWidgets.append(widget)

    def createToolbarsMenu(self, menu):
        self.removeActions(menu.actions())
        menu.clear()

        action = menu.addAction('&Menu Bar', self.toggleShowMenubar)
        action.setCheckable(True)
        action.setChecked(self.menuBar().isVisible())

        action = menu.addAction('&Navigation Toolbar', self.toggleShowNavigationToolbar)
        action.setCheckable(True)
        action.setChecked(self._navigationToolbar.isVisible())

        action = menu.addAction('&Bookmarks Toolbar', self.toggleShowBookmarksToolbar)
        action.setCheckable(True)
        action.setChecked(Settings().value('Browser-View-Settings/showBookmarksToolbar', type=bool))

        menu.addSeparator()

        action = menu.addAction('&Tabs on Top', self.toggleTabsOnTop)
        action.setCheckable(True)
        action.setChecked(gVar.appSettings.tabsOnTop)

        self.addActions(menu.actions())

    def createSidebarsMenu(self, menu):
        self._sideBarManager.createMenu(menu)

    def createEncodingMenu(self, menu):
        isoCodecs = []
        utfCodecs = []
        windowsCodecs = []
        isciiCodecs = []
        ibmCodecs = []
        otherCodecs = []
        allCodecs = []

        for mib in QTextCodec.availableMibs():
            codecName = QTextCodec.codecForMib(mib).name()
            codecName = codecName.data().decode('utf8')
            if codecName in allCodecs:
                continue
            allCodecs.append(codecName)
            if codecName.startswith('ISO'):
                isoCodecs.append(codecName)
            elif codecName.startswith('UTF'):
                utfCodecs.append(codecName)
            elif codecName.startswith('windows'):
                windowsCodecs.append(codecName)
            elif codecName.startswith('Iscii'):
                isciiCodecs.append(codecName)
            elif codecName.startswith('IBM'):
                ibmCodecs.append(codecName)
            else:
                otherCodecs.append(codecName)

        if not menu.isEmpty():
            menu.addSeperator()

        self._createEncodingSubMenu('ISO', isoCodecs, menu)
        self._createEncodingSubMenu('UTF', utfCodecs, menu)
        self._createEncodingSubMenu('Windows', windowsCodecs, menu)
        self._createEncodingSubMenu('Iscii', isciiCodecs, menu)
        self._createEncodingSubMenu('IBM', ibmCodecs, menu)
        self._createEncodingSubMenu('Other', otherCodecs, menu)

    def removeActions(self, actions):
        '''
        @param: actions QList<QAction*>
        '''
        for action in actions:
            self.removeAction(action)

    def addSideBar(self):
        '''
        @return SideBar*
        '''
        if self._sideBar:
            return self._sideBar
        self._sideBar = SideBar(self._sideBarManager, self)
        self._mainSplitter.insertWidget(0, self._sideBar)
        self._mainSplitter.setCollapsible(0, False)
        self._mainLayout.setSizes([self._sideBarWidth, self._webViewWidth])
        return self._sideBar

    def saveSideBarSettings(self):
        if self._sideBar:
            # That +1 is important here, without it, the sidebar width would
            # decrease by 1 pixel every close
            self._sideBarWidth = self._mainSplitter.sizes()[0] + 1
            self._webViewWidth = self.width() - self._sideBarWidth
        Settings().setValue('Browser-View-Settings/SideBar', self._sideBarManager.activeSideBar())

    def tabCount(self):
        return self._tabWidget.count()

    def weView(self):
        '''
        @return TabbedWebView
        '''
        return self.weViewByIndex(self._tabWidget.currentIndex())

    def weViewByIndex(self, index):
        '''
        @return TabbedWebView
        '''
        webTab = self._tabWidget.widget(index)
        if not webTab:
            return None
        return webTab.webView()

    def windowType(self):
        '''
        @return const.BrowserWindowType
        '''
        return self._windowType

    def locationBar(self):
        '''
        @return LocationBar
        '''
        return self._tabWidget.locationBars().currentWidget()

    def tabWidget(self):
        return self._tabWidget

    def bookmarksToolbar(self):
        '''
        @return BookmarksToolbar
        '''
        return self._bookmarksToolbar

    def statusBar(self):
        '''
        @return StatusBar
        '''
        return self._statusBar

    def navigationBar(self):
        '''
        @return NavigationBar
        '''
        return self._navigationToolbar

    def sideBarManager(self):
        '''
        @return SideBarManager
        '''
        return self._sideBarManager

    def ipLabel(self):
        '''
        @return QLabel
        '''
        return self._ipLabel

    def superMenu(self):
        '''
        @return QMenu
        '''
        return self._superMenu

    def homepageUrl(self):
        return self._homepage

    def action(self, name):
        '''
        @return QAction
        '''
        return self._mainMenu.action(name)

    def tabModel(self):
        '''
        @return TabModel
        '''
        return self._tabModel

    def tabMruModel(self):
        '''
        @return TabMruModel
        '''
        return self._tabMruModel

    # public Q_SIGNALS:
    startingCompleted = pyqtSignal()
    aboutToClose = pyqtSignal()

    # public Q_SLOTS:
    def addTab(self):
        self._tabWidget.addViewByUrl(QUrl(), const.NT_SelectedNewEmptyTab, True)
        self._tabWidget.setCurrentTabFresh(True)

        if self.isFullScreen():
            self.showNavigationWithFullScreen()

    def goHome(self):
        self.loadAddress(self._homepage)

    def goHomeInNewTab(self):
        self._tabWidget.addViewByUrl(self._homepage, const.NT_SelectedTab)

    def goBack(self):
        self.weView().back()

    def goForward(self):
        self.weView().forward()

    def reload(self):
        self.weView().reload()

    def reloadBypassCache(self):
        self.weView().reloadBypassCache()

    def setWindowTitle(self, title):
        if gVar.app.isPrivate():
            title = '%s (Private Browsing)' % title
        super().setWindowTitle(title)

    def showWebInspector(self):
        webView = self.weView()
        if webView and webView.webTab():
            webView.webTab().showWebInspector()

    def toggleWebInspector(self):
        webView = self.weView()
        if webView and webView.webTab():
            webView.webTab().toggleWebInspector()

    def showHistoryManager(self):
        gVar.app.browsingLibrary().showHistory(self)

    def toggleShowMenubar(self):
        self.setUpdatesEnabled(False)
        menuBar = self.menuBar()
        menuBar.setVisible(not menuBar.isVisible())
        self._navigationToolbar.setSuperMenuVisible(not menuBar.isVisible())
        self.setUpdatesEnabled(True)

        Settings().setValue('Browser-View-Settings/showMenuBar', menuBar.isVisible())

        # Make sure we show Navigation Toolbar when Menu Bar is hidden
        if not self._navigationToolbar.isVisible() and not menuBar.isVisible():
            self.toggleShowNavigationToolbar()

    def toggleShowStatusBar(self):
        self.setUpdatesEnabled(False)
        self._statusBar.setVisible(not self._statusBar.isVisible())
        self.setUpdatesEnabled(True)
        Settings().setValue('Browser-View-Settings/showStatusBar', self._statusBar.isVisible())

    def toggleShowBookmarksToolbar(self):
        self.setUpdatesEnabled(False)
        self._bookmarksToolbar.setVisible(not self._bookmarksToolbar.isVisible())
        self.setUpdatesEnabled(True)
        Settings().setValue('Browser-View-Settings/showBookmarksToolbar', self._bookmarksToolbar.isVisible())
        Settings().setValue('Browser-View-Settings/instantBookmarksToolbar', False)

    def toggleShowNavigationToolbar(self):
        self.setUpdatesEnabled(False)
        self._navigationToolbar.setVisible(not self._navigationToolbar.isVisible())
        self.setUpdatesEnabled(True)
        Settings().setValue('Browser-View-Settings/showNavigationToolbar', self._navigationToolbar.isVisible())

        # Make sure we show Navigation Toolbar when Menu Bar is hidden
        if not self._navigationToolbar.isVisible() and not self.menuBar().isVisible():
            self.toggleShowMenubar()

    def toggleTabsOnTop(self, enable):
        gVar.appSettings.tabsOnTop = enable
        self._navigationContainer.toggleTabsOnTop(enable)

    def toggleFullScreen(self):
        if self._htmlFullScreenView:
            self.weView().triggerPageAction(QWebEnginePage.ExitFullScreen)
            return
        if self.isFullScreen():
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
        else:
            self.setWindowState(self.windowState() | Qt.WindowFullScreen)

    def requestHtmlFullScreen(self, view, enable):
        '''
        @param: view TabbedWebView
        @param: enable bool
        '''
        if enable:
            self.setWindowState(self.windowState() | Qt.WindowFullScreen)
        else:
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
        if self._sideBar:
            self._sideBar.data().setHidden(enable)
        self._htmlFullScreenView = enable and view or None

    def loadActionUrl(self, obj=None):
        if not obj:
            obj = self.sender()
        # TODO: QAction* action = qobject_cast<QAction*>(obj)
        action = obj
        if action:
            self.loadAddress(action.data().toUrl())

    def loadActionUrlInNewTab(self, obj=None):
        if not obj:
            obj = self.sender()
        # TODO: QAction* action = qobject_cast<QAction*>(obj)
        action = obj
        if action:
            self.loadAddress(action.data().toUrl(), const.NT_SelectedTabAtTheEnd)

    def bookmarkPage(self):
        view = self.weView()
        BookmarksTools.addBookmarkDialog(self, view.url(), view.title())

    def bookmarkAllTabs(self):
        BookmarksTools.bookmarkAllTabsDialog(self, self._tabWidget)

    def loadAddress(self, url):
        webView = self.weView()
        if webView.webTab().isPinned():
            index = self._tabWidget.addViewByUrl(url, gVar.appSettings.newTabPosition)
            self.weView(index).setFocus()
        else:
            webView.setFocus()
            url = 'http://www.baidu.com'
            webView.loadByReq(LoadRequest(url))

    def showSource(self, view=None):
        if not view:
            return
        view.showSource()

    # private Q_SLOTS:
    def _openLocation(self):
        if self.isFullScreen():
            self.showNavigationWithFullScreen()
        self.locationBar().setFocus()
        self.locationBar().selectAll()

    def _openFile(self):
        fileTypes = ("%s(*.html *.htm *.shtml *.shtm *.xhtml);;"
            "%s(*.png *.jpg *.jpeg *.bmp *.gif *.svg *.tiff);;"
            "%s(*.txt);;"
            "%s(*.*)")
        fileTypes % ("HTML files", "Image files", "Text files", "All files")
        filePath = gVar.appTools.getOpenFileName("MainWindow-openFile",
            self, "Open file...", QDir.homePath(), fileTypes)

        if filePath:
            self.loadAddress(QUrl.fromLocalFile(filePath))

    def _closeWindow(self):
        if const.OS_MAC:
            self.close()
            return
        if gVar.app.windowCount() > 1:
            self.close()

    def _closeTab(self):
        # Don't close pinned tabs with keyboard shortcuts (Ctrl+w, Ctrl+F4)
        webView = self.weView()
        if webView and not webView.webTab().isPinned():
            self._tabWidget.requestCloseTab()

    def _loadSettings(self):
        settings = Settings()
        # Url settings
        settings.beginGroup('Web-URL-Settings')
        self._homepage = settings.value('homepage', 'app:start', type=QUrl)
        settings.endGroup()
        # Browser Window settings
        settings.beginGroup('Browser-View-Settings')
        showStatusBar = settings.value('showStatusBar', False, type=bool)
        showBookmarksToolbar = settings.value('showBookmarksToolbar', False, type=bool)
        showNavigationToolbar = settings.value('showNavigationToolbar', True, type=bool)
        showMenuBar = settings.value('showMenuBar', False, type=bool)
        # Make sure both menubar and navigationbar are not hidden
        if not showNavigationToolbar:
            showMenuBar = True
            settings.setValue('showMenubar', True)
        settings.endGroup()

        settings.beginGroup('Shortcuts')
        self._useTabNumberShortcuts = settings.value('useTabNumberShortcuts', True, type=bool)
        self._useSpeedDialNumberShortcuts = settings.value('useSpeedDialNumberShortcuts', True, type=bool)
        self._useSingleKeyShortcuts = settings.value('useSingleKeyShortcuts', False, type=bool)
        settings.endGroup()

        settings.beginGroup('Web-Browser-Settings')
        quitAction = self._mainMenu.action('Standard/Quit')
        if settings.value('closeAppWithCtrlQ', True, type=bool):
            quitAction.setShortcut(gVar.appTools.actionShortcut(QKeySequence.Quit, QKeySequence('Ctrl+Q')))
        else:
            quitAction.setShortcut(QKeySequence())
        settings.endGroup()

        self._statusBarVisible = showStatusBar
        self.statusBar().setVisible(not self.isFullScreen() and showStatusBar)
        self._bookmarksToolbar.setVisible(showBookmarksToolbar)
        self._navigationToolbar.setVisible(showNavigationToolbar)
        if not const.OS_MACOS:
            self._menuBarVisible = showMenuBar
            self.menuBar().setVisible(not self.isFullScreen() and showMenuBar)
        showSuperMenu = self.isFullScreen() or not showMenuBar
        # TODO: debug code
        showSuperMenu = True
        self._navigationToolbar.setSuperMenuVisible(showSuperMenu)

    def _postLaunch(self):  # noqa C901
        self._loadSettings()
        addTab = True
        startUrl = QUrl()

        from .MainApplication import MainApplication
        afterLaunch = gVar.app.afterLaunch()
        if afterLaunch == MainApplication.OpenBlankPage:
            pass
        elif afterLaunch == MainApplication.OpenSpeedDial:
            startUrl = 'app:speeddial'
        elif afterLaunch in (MainApplication.OpenHomePage,
                MainApplication.RestoreSession,
                MainApplication.SelectSession):
            startUrl = self._homepage

        if not gVar.app.isTestModeEnabled():
            self.show()

        if self._windowType == const.BW_FirstAppWindow:
            if gVar.app.isStartingAfterCrash():
                addTab = False
                startUrl.clear()
                self._tabWidget.addViewByUrl(QUrl('app:restore'), const.NT_CleanSelectedTabAtTheEnd)
            elif afterLaunch in (MainApplication.SelectSession, MainApplication.RestoreSession):
                addTab = self._tabWidget.count() <= 0
        elif self._windowType in (const.BW_NewWindow, const.BW_MacFirstWindow):
            addTab = True
        elif self._windowType == const.BW_OtherRestoredWindow:
            addTab = False

        if not self._startUrl.isEmpty():
            startUrl = self._startUrl
            addTab = True
        if self._startTab:
            addTab = False
            self._tabWidget.addViewByTab(self._startTab, const.NT_SelectedTab)
        if self._startPage:
            addTab = False
            self._tabWidget.addViewByUrl(QUrl())
            self.weView().setPage(self._startPage)
        if addTab:
            self._tabWidget.addViewByUrl(startUrl, const.NT_CleanSelectedTabAtTheEnd)
            if not startUrl or startUrl == 'app:speeddial':
                self.locationBar().setFocus()
        # Someting went really wrong .. add one tab
        if self._tabWidget.count() <= 0:
            self._tabWidget.addViewByUrl(self._homepage, const.NT_SelectedTabAtTheEnd)

        gVar.app.plugins().emitMainWindowCreated(self)
        self.startingCompleted.emit()

        self.raise_()
        self.activateWindow()
        self._updateStartupFocus()

    def _webSearch(self):
        self._navigationToolbar.webSearchBar().setFocus()
        self._navigationToolbar.webSearchBar().selectAll()

    def _searchOnPage(self):
        webView = self.weView()
        if webView and webView.webTab():
            searchText = webView.page().selectedText()
            if '\n' not in searchText:
                webView.webTab().showSearchToolBar(searchText)
            else:
                webView.webTab().showSearchToolBar()

    def _changeEncoding(self):
        action = self.sender()
        if action:
            encoding = action.data()
            gVar.app.webSettings().setDefaultTextEncoding(encoding)
            Settings().setValue('Web-Browser-Settings/DefaultEncoding', encoding)
            self.weView().reload()

    def _printPage(self):
        self.weView().printPage()

    def _saveSettings(self):
        if gVar.app.isPrivate():
            return
        settings = Settings()
        settings.beginGroup('Browser-View-Settings')
        settings.setValue('WindowGeometry', self.saveGeometry())

        state = self._saveUiState()
        for key, val in state.items():
            settings.setValue(key, val)

        settings.endGroup()

    def _hideNavigationSlot(self):
        view = self.weView()
        mouseInView = view and view.underMouse()
        if self.isFullScreen() and mouseInView:
            self._navigationContainer.hide()

    # private
    # override
    def event(self, event):
        '''
        @param: event QEvent
        '''
        if event.type() == QEvent.WindowStateChange:
            # TODO: QWindowStateChangeEvent *e = static_cast<QWindowStateChangeEvent*>(event);
            e = event
            if not (e.oldState() & Qt.WindowFullScreen) and (self.windowState() & Qt.WindowFullScreen):
                # Enter fullscreen
                self._statusBarVisible = self._statusBar.isVisible()
                self._menuBarVisible = self.menuBar().isVisible()
                self.menuBar().hide()
                self._statusBar.hide()

                self._navigationContainer.hide()
                self._navigationToolbar.enterFullScreen()

                # Show main menu button since menubar is hidden
                self._navigationToolbar.setSuperMenuVisible(True)
            elif (e.oldState() & Qt.WindowFullScreen) and not (self.windowState() & Qt.WindowFullScreen):
                # Leave fullscreen
                self._statusBar.setVisible(self._statusBarVisible)
                self.menuBar().setVisible(self._menuBarVisible)

                self._navigationContainer.show()
                self._navigationToolbar.setSuperMenuVisible(not self._menuBarVisible)
                self._navigationToolbar.leaveFullScreen()
                self._htmlFullScreenView = None

            if self._hideNavigationTimer:
                self._hideNavigationTimer.stop()

        return super().event(event)

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        self._bookmarksToolbar.setMaximumWidth(self.width())
        super().resizeEvent(event)

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        # TODO:
        pass

    # override
    def keyReleaseEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        # TODO
        pass

    # override
    def closeEvent(self, event):
        '''
        @param: event QCloseEvent
        '''
        if gVar.app.isClosing():
            self._saveSettings()
            return
        settings = Settings()
        askOnClose = settings.value('Browser-Tabs-Settings/AskOnClosing', True, type=bool)

        from .MainApplication import MainApplication
        if gVar.app.afterLaunch() in (MainApplication.SelectSession,
                MainApplication.RestoreSession) and gVar.app.windowCount() == 1:
            askOnClose = False

        if askOnClose and self._tabWidget.normalTabsCount() > 1:
            dialog = CheckBoxDialog(QMessageBox.Yes | QMessageBox.No, self)
            dialog.setDefaultButton(QMessageBox.No)
            dialog.setText(
                "There are still %s open tabs and your session won't be stored.\n" % self._tabWidget.count() +
                "Are you sure you want to close this window?")
            dialog.setCheckBoxText("Don't ask again")
            dialog.setWindowTitle('There are still open tabs')
            dialog.setIcon(QMessageBox.Warning)
            if dialog.exec_() != QMessageBox.Yes:
                event.ignore()
                return
            if dialog.isChecked():
                settings.setValue('Browser-Tabs-Settings/AskOnClosing', False)

        self.aboutToClose.emit()

        self._saveSettings()
        gVar.app.closedWindowsManager().saveWindow(self)
        if gVar.app.windowCount() == 1:
            gVar.app.quitApplication()

        event.accept()

    # == private ==
    def _setupUi(self):
        settings = Settings()
        settings.beginGroup('Browser-View-Settings')
        windowGeometry = settings.value('WindowGeometry', b'')

        keys = [
            ('LocationBarWidth', int),
            ('WebSearchBarWidth', int),
            ('SideBarWidth', int),
            ('WebViewWidth', int),
            ('SideBar', str),
        ]

        uiState = {}
        for key, typ in keys:
            if settings.contains(key):
                uiState[key] = typ(settings.value(key))

        settings.endGroup()

        widget = QWidget(self)
        widget.setCursor(Qt.ArrowCursor)
        self.setCentralWidget(widget)

        self._mainLayout = QVBoxLayout(widget)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(0)
        self._mainSplitter = QSplitter(self)
        self._mainSplitter.setObjectName('sidebar-splitter')
        self._tabWidget = TabWidget(self)
        self._superMenu = QMenu(self)
        self._navigationToolbar = NavigationBar(self)
        self._bookmarksToolbar = BookmarksToolbar(self)

        self._tabModel = TabModel(self, self)
        self._tabMruModel = TabMruModel(self, self)
        self._tabMruModel.setSourceModel(self._tabModel)

        self._navigationContainer = NavigationContainer(self)
        self._navigationContainer.addWidget(self._navigationToolbar)
        self._navigationContainer.addWidget(self._bookmarksToolbar)
        self._navigationContainer.setTabBar(self._tabWidget.tabBar())

        self._mainSplitter.addWidget(self._tabWidget)
        self._mainSplitter.setCollapsible(0, False)

        self._mainLayout.addWidget(self._navigationContainer)
        self._mainLayout.addWidget(self._mainSplitter)

        self._statusBar = StatusBar(self)
        self._statusBar.setObjectName('mainwindow-statusbar')
        self._statusBar.setCursor(Qt.ArrowCursor)
        self.setStatusBar(self._statusBar)
        self._progressBar = ProgressBar(self._statusBar)
        self._ipLabel = QLabel(self)
        self._ipLabel.setObjectName('statusbar-ip-label')
        self._ipLabel.setToolTip('IP Address of current page')

        self._statusBar.addPermanentWidget(self._progressBar)
        self._statusBar.addPermanentWidget(self.ipLabel())

        downloadsButton = DownloadsButton(self)
        self._statusBar.addButton(downloadsButton)
        self._navigationToolbar.addToolButton(downloadsButton)

        desktop = gVar.app.desktop()
        windowWidth = desktop.availableGeometry().width() / 1.3
        windowHeight = desktop.availableGeometry().height() / 1.3

        # Let the WM decides where to put new browser window
        if self._windowType not in (const.BW_FirstAppWindow, const.BW_MacFirstWindow) and \
                gVar.app.getWindow():
            if const.OS_WIN:
                # Windows WM places every new window in the middle of screen .. for some reason
                p = gVar.app.getWindow().geometry().topLeft()
                p.setX(p.x() + 30)
                p.setY(p.y() + 30)
                if not desktop.availableGeometry(gVar.app.getWindow()).contains(p):
                    p.setX(desktop.availableGeometry(gVar.app.getWindow()).x() + 30)
                    p.setY(desktop.availableGeometry(gVar.app.getWindow()).y() + 30)
                self.setGeometry(QRect(p, gVar.app.getWindow().size()))
            else:
                self.resize(gVar.app.getWindow().size())
        elif not self.restoreGeometry(windowGeometry):
            if const.OS_WIN:
                self.setGeometry(QRect(desktop.availableGeometry(gVar.app.getWindow()).x() + 30,
                    desktop.availableGeometry(gVar.app.getWindow()).y() + 30, windowWidth, windowHeight))
            else:
                self.resize(windowWidth, windowHeight)

        self._restoreUiState(uiState)
        # Set some sane minimum width
        self.setMinimumWidth(300)

    def _setupMenu(self):
        if const.OS_MACOS:
            macMainMenu = None
            if not macMainMenu:
                macMainMenu = MainMenu(self, 0)
                macMainMenu.initMenuBar(QMenuBar(0))
                gVar.app.activeWindowChanged.connect(macMainMenu.setWindow)
            else:
                macMainMenu.setWindow(self)
        else:
            self.setMenuBar(MenuBar(self))
            self._mainMenu = MainMenu(self, self)
            self._mainMenu.initMenuBar(self.menuBar())

        self._mainMenu.initSuperMenu(self._superMenu)

        # Setup other shortcuts
        reloadBypassCacheAction = QShortcut(QKeySequence('Ctrl+F5'), self)
        reloadBypassCacheAction2 = QShortcut(QKeySequence('Ctrl+Shift+R'), self)
        reloadBypassCacheAction.activated.connect(self.reloadBypassCache)
        reloadBypassCacheAction2.activated.connect(self.reloadBypassCache)

        closeTabAction = QShortcut(QKeySequence('Ctrl+W'), self)
        closeTabAction2 = QShortcut(QKeySequence('Ctrl+F4'), self)

        closeTabAction.activated.connect(self._closeTab)
        closeTabAction2.activated.connect(self._closeTab)

        reloadAction = QShortcut(QKeySequence('Ctrl+R'), self)
        reloadAction.activated.connect(self.reload)

        openLocationAction = QShortcut(QKeySequence('Alt+D'), self)
        openLocationAction.activated.connect(self._openLocation)

        inspectorAction = QShortcut(QKeySequence('F12'), self)
        inspectorAction.activated.connect(self.toggleWebInspector)

        restoreClosedWindow = QShortcut(QKeySequence('Ctrl+Shift+N'), self)
        restoreClosedWindow.activated.connect(gVar.app.closedWindowsManager().restoreClosedWindow)

    def _updateStartupFocus(self):
        def _updateStartupFocusCb():
            # Scroll to current tab
            self.tabWidget().tabBar().ensureVisible()
            # Update focus
            page = self.weView().page()
            url = page.requestedUrl()
            if not self._startPage and not LocationBar.convertUrlToText(url):
                self.locationBar().setFocus()
            else:
                self.weView().setFocus()
        QTimer.singleShot(500, _updateStartupFocusCb)

    def _createEncodingAction(self, codecName, activeCodecName, menu):
        '''
        @param: codecName QString
        @param: activeCodecName QString
        @param: menu QMenu
        '''
        action = QAction(codecName, menu)
        action.setData(codecName)
        action.setCheckable(True)
        action.triggered.connect(self._changeEncoding)
        if activeCodecName.lower() == codecName.lower():
            action.setChecked(True)
        return action

    def _createEncodingSubMenu(self, name, codecNames, menu):
        '''
        @param: name QString
        @param: codecName QStringList
        @param: menu QMenu
        '''
        if not codecNames:
            return

        codecNames.sort()
        subMenu = QMenu(name, menu)
        activeCodecName = gVar.app.webSettings().defaultTextEncoding()

        group = QActionGroup(subMenu)

        for codecName in codecNames:
            act = self._createEncodingAction(codecName, activeCodecName, subMenu)
            group.addAction(act)
            subMenu.addAction(act)

        menu.addMenu(subMenu)

    def _saveUiState(self):
        '''
        @return: QHash<QStirng, QVariant>
        '''
        self.saveSideBarSettings()
        state = {}
        state['LocationBarWidth'] = self._navigationToolbar.splitter().sizes()[0]
        state['WebSearchBarWidth'] = self._navigationToolbar.splitter().sizes()[1]
        state['SideBarWidth'] = self._sideBarWidth
        state['WebViewWidth'] = self._webViewWidth
        state['SideBar'] = self._sideBarManager.activeSideBar()
        return state

    def _restoreUiState(self, state):
        '''
        @param: state QHash<QString, QVariant>
        '''
        locationBarWidth = state.get('LocationBarWidth', 480)
        webSearchBarWidth = state.get('WebSearchBarWidth', 140)
        self._navigationToolbar.setSplitterSizes(locationBarWidth, webSearchBarWidth)

        self._sideBarWidth = state.get('SideBarWidth', 250)
        self._webViewWidth = state.get('WebViewWidth', 2000)
        if self._sideBar:
            self._mainSplitter.setSizes([self._sideBarWidth, self._webViewWidth])
        activeSideBar = state.get('SideBar')
        if not activeSideBar and self._sideBar:
            self._sideBar.close()
        else:
            self._sideBarManager.showSideBar(activeSideBar, False)
