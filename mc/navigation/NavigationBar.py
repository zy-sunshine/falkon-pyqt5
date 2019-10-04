from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QHBoxLayout
from PyQt5.Qt import QStyle
from mc.tools.ToolButton import ToolButton
from PyQt5.Qt import Qt
from .ReloadStopButton import ReloadStopButton
from mc.tools.EnhancedMenu import Menu, Action
from PyQt5.QtWidgets import QToolButton
from PyQt5.QtWidgets import QSplitter
from PyQt5.Qt import QSizePolicy
from .WebSearchBar import WebSearchBar
from mc.app.Settings import Settings
from .NavigationBarToolButton import NavigationBarToolButton
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.common.globalvars import gVar
from mc.common import const
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QIcon
from PyQt5.QtWidgets import QMenu
from .NavigationBarConfigDialog import NavigationBarConfigDialog
from mc.tools.AbstractButtonInterface import AbstractButtonInterface
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QAction

class NavigationBar(QWidget):

    class WidgetData:
        def __init__(self):
            self.id = ''
            self.name = ''
            self.widget = None  # QWidget
            self.button = None  # AbstractButtonInterface

    def __init__(self, window):
        super(NavigationBar, self).__init__(window)
        self._window = window
        self._layout = None  # QHBoxLayout
        self._navigationSplitter = None  # QSplitter
        self._searchLine = None  # WebSearchBar

        self._menuBack = None  # Menu
        self._menuForward = None  # Menu
        self._buttonBack = None  # ToolButton
        self._buttonForward = None  # ToolButton
        self._reloadStop = None  # ReloadStopButton
        self._menuTools = None  # Menu
        self._supMenu = None  # ToolButton
        self._exitFullscreen = None  # ToolButton
        self._backConnection = None  # QMetaObject::Conection
        self._forwardConnection = None  # QMetaObject::Connection

        self._layoutIds = []  # QStringList
        self._widgets = {}  # QHash<QString, WidgetData>

        self.setObjectName('navigationBar')
        self._layout = QHBoxLayout(self)
        style = self.style()

        # TODO:
        margin = style.pixelMetric(QStyle.PM_ToolBarItemMargin, None, self) + \
            style.pixelMetric(QStyle.PM_ToolBarFrameWidth, None, self)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(style.pixelMetric(QStyle.PM_ToolBarItemSpacing, None, self))
        self.setLayout(self._layout)

        self._buttonBack = ToolButton(self)
        self._buttonBack.setObjectName('navigation-button-back')
        self._buttonBack.setToolTip('Back')
        self._buttonBack.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self._buttonBack.setToolbarButtonLook(True)
        self._buttonBack.setShowMenuOnRightClick(True)
        self._buttonBack.setAutoRaise(True)
        self._buttonBack.setEnabled(False)
        self._buttonBack.setFocusPolicy(Qt.NoFocus)

        self._buttonForward = ToolButton(self)
        self._buttonForward.setObjectName('navigation-button-next')
        self._buttonForward.setToolTip('Forward')
        self._buttonForward.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self._buttonForward.setToolbarButtonLook(True)
        self._buttonForward.setShowMenuOnRightClick(True)
        self._buttonForward.setAutoRaise(True)
        self._buttonForward.setEnabled(False)
        self._buttonForward.setFocusPolicy(Qt.NoFocus)

        backNextLayout = QHBoxLayout()
        backNextLayout.setContentsMargins(0, 0, 0, 0)
        backNextLayout.setSpacing(0)
        backNextLayout.addWidget(self._buttonBack)
        backNextLayout.addWidget(self._buttonForward)
        backNextWidget = QWidget(self)
        backNextWidget.setLayout(backNextLayout)

        self._reloadStop = ReloadStopButton(self)

        buttonHome = ToolButton(self)
        buttonHome.setObjectName('navigation-button-home')
        buttonHome.setToolTip('Home')
        buttonHome.setToolButtonStyle(Qt.ToolButtonIconOnly)
        buttonHome.setToolbarButtonLook(True)
        buttonHome.setAutoRaise(True)
        buttonHome.setFocusPolicy(Qt.NoFocus)

        buttonAddTab = ToolButton(self)
        buttonAddTab.setObjectName('navigation-button-addtab')
        buttonAddTab.setToolTip('New Tab')
        buttonAddTab.setToolButtonStyle(Qt.ToolButtonIconOnly)
        buttonAddTab.setToolbarButtonLook(True)
        buttonAddTab.setAutoRaise(True)
        buttonAddTab.setFocusPolicy(Qt.NoFocus)

        self._menuBack = Menu(self)
        self._menuBack.setCloseOnMiddleClick(True)
        self._buttonBack.setMenu(self._menuBack)
        self._buttonBack.aboutToShowMenu.connect(self._aboutToShowHistoryBackMenu)

        self._menuForward = Menu(self)
        self._menuForward.setCloseOnMiddleClick(True)
        self._buttonForward.setMenu(self._menuForward)
        self._buttonForward.aboutToShowMenu.connect(self._aboutToShowHistoryNextMenu)

        buttonTools = ToolButton(self)
        buttonTools.setObjectName('navigation-button-tools')
        buttonTools.setPopupMode(QToolButton.InstantPopup)
        buttonTools.setToolbarButtonLook(True)
        buttonTools.setToolTip('Tools')
        buttonTools.setAutoRaise(True)
        buttonTools.setFocusPolicy(Qt.NoFocus)
        buttonTools.setShowMenuInside(True)

        self._menuTools = Menu(self)
        buttonTools.setMenu(self._menuTools)
        buttonTools.aboutToShowMenu.connect(self._aboutToShowToolsMenu)

        self._supMenu = ToolButton(self)
        self._supMenu.setObjectName('navigation-button-supermenu')
        self._supMenu.setPopupMode(QToolButton.InstantPopup)
        self._supMenu.setToolbarButtonLook(True)
        self._supMenu.setToolTip('Main Menu')
        self._supMenu.setAutoRaise(True)
        self._supMenu.setFocusPolicy(Qt.NoFocus)
        self._supMenu.setMenu(self._window.superMenu())
        self._supMenu.setShowMenuInside(True)

        self._searchLine = WebSearchBar(self._window)

        self._navigationSplitter = QSplitter(self)
        self._navigationSplitter.addWidget(self._window.tabWidget().locationBars())
        self._navigationSplitter.addWidget(self._searchLine)

        self._navigationSplitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._navigationSplitter.setCollapsible(0, False)

        self._exitFullscreen = ToolButton(self)
        self._exitFullscreen.setObjectName('navigation-button-exitfullscreen')
        self._exitFullscreen.setToolTip('Exit Fullscreen')
        self._exitFullscreen.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self._exitFullscreen.setToolbarButtonLook(True)
        self._exitFullscreen.setFocusPolicy(Qt.NoFocus)
        self._exitFullscreen.setAutoRaise(True)
        self._exitFullscreen.setVisible(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenuRequested)

        self._buttonBack.clicked.connect(self.goBack)
        self._buttonBack.middleMouseClicked.connect(self.goBackInNewTab)
        self._buttonBack.controlClicked.connect(self.goBackInNewTab)
        self._buttonForward.clicked.connect(self.goForward)
        self._buttonForward.middleMouseClicked.connect(self.goForwardInNewTab)
        self._buttonForward.controlClicked.connect(self.goForwardInNewTab)

        self._reloadStop.stopClicked.connect(self.stop)
        self._reloadStop.reloadClicked.connect(self.reload)
        buttonHome.clicked.connect(self._window.goHome)
        buttonHome.middleMouseClicked.connect(self._window.goHomeInNewTab)
        buttonHome.controlClicked.connect(self._window.goHomeInNewTab)
        buttonAddTab.clicked.connect(self._window.addTab)
        buttonAddTab.middleMouseClicked.connect(self._window.tabWidget().addTabFromClipboard)
        self._exitFullscreen.clicked.connect(self._window.toggleFullScreen)

        self._addWidget(backNextWidget, 'button-backforward', 'Back and Forward buttons')
        self._addWidget(self._reloadStop, 'button-reloadstop', 'Reload button')
        self._addWidget(buttonHome, 'button-home', 'Home button')
        self._addWidget(buttonAddTab, 'button-addtab', 'Add tab button')
        self._addWidget(self._navigationSplitter, 'locationbar', 'Address and Search bar')
        self._addWidget(buttonTools, 'button-tools', 'Tools button')
        self._addWidget(self._exitFullscreen, 'button-exitfullscreen', 'Exit Fullscreen button')

        self._loadSettings()

    def setSplitterSizes(self, locationBar, websearchBar):
        '''
        @param: locationBar int
        @param: websearchBar int
        '''
        sizes = []

        if locationBar == 0:
            splitterWidth = self._navigationSplitter.width()
            sizes.append(int(float(splitterWidth) * 0.80))
            sizes.append(int(float(splitterWidth) * 0.20))
        else:
            sizes.append(locationBar)
            sizes.append(websearchBar)

        self._navigationSplitter.setSizes(sizes)

    def setCurrentView(self, view):
        '''
        @param: view TabbedWebView
        '''
        for data in self._widgets.values():
            if data.button:
                data.button.setWebView(view)

        if not view:
            return

        self._connectPageActions(view.page())
        view.pageChanged.connect(self._connectPageActions)

    def _connectPageActions(self, page):
        '''
        @param: page QWebEnginePage
        '''
        def updateButton(button, action):
            '''
            @param: button ToolButton
            @param: action QAction
            '''
            button.setEnabled(action.isEnabled())

        def updateBackButton():
            updateButton(self._buttonBack, page.action(QWebEnginePage.Back))

        def updateForwardButton():
            updateButton(self._buttonForward, page.action(QWebEnginePage.Forward))

        updateBackButton()
        updateForwardButton()

        if self._backConnection:
            #self._backConnection.disconnect()
            self._connPage.action(QWebEnginePage.Back).changed.disconnect(self._backConnection)
        if self._forwardConnection:
            #self._forwardConnection.disconnect()
            self._connPage.action(QWebEnginePage.Forward).changed.disconnect(self._forwardConnection)
        self._backConnection = page.action(QWebEnginePage.Back).changed.connect(updateBackButton)
        self._forwardConnection = page.action(QWebEnginePage.Forward).changed.connect(updateForwardButton)
        self._connPage = page

    def showReloadButton(self):
        self._reloadStop.showReloadButton()

    def showStopButton(self):
        self._reloadStop.showStopButton()

    def enterFullScreen(self):
        if self._layout.indexOf(self._exitFullscreen) != -1:
            self._exitFullscreen.show()

    def leaveFullScreen(self):
        if self._layout.indexOf(self._exitFullscreen) != -1:
            self._exitFullscreen.hide()

    def webSearchBar(self):
        '''
        @return: WebSearchBar
        '''
        return self._searchLine

    def splitter(self):
        '''
        @return QSplitter
        '''
        return self._navigationSplitter

    def setSuperMenuVisible(self, visible):
        self._supMenu.setVisible(visible)

    def layoutMargin(self):
        return self._layout.getContentsMargins().left()

    def setLayoutMargin(self, margin):
        self._layout.setContentsMargins(margin, margin, margin, margin)

    def _addWidget(self, widget, id_, name):
        if not widget or not id_ or not name:
            return

        data = self.WidgetData()
        data.id = id_
        data.name = name
        data.widget = widget
        self._widgets[id_] = data

    def addWidget(self, widget, id_, name):
        '''
        @param: widget QWidget
        @param: id_ QString
        @param: name QString
        '''
        self._addWidget(widget, id_, name)
        self._reloadLayout()

    def removeWidget(self, id_):
        '''
        @param: id_ QString
        '''
        if id_ not in self._widgets:
            return

        self._widgets.pop(id_)
        self._reloadLayout()

    def addToolButton(self, button):
        '''
        @param: button AbstractButtonInterface
        '''
        if not button or not button.isValid():
            return

        toolButton = NavigationBarToolButton(button, self)
        toolButton.setProperty('button-id', button.id())

        def x(self):
            if self._layout.indexOf(toolButton) != -1:
                toolButton.updateVisibility()
        toolButton.visibilityChangedRequested.connect(x)

        data = self.WidgetData()
        data.id = button.id()
        data.name = button.name()
        data.widget = toolButton
        data.button = button
        self._widgets[data.id] = data

        data.button.setWebView(self._window.weView())

        self._reloadLayout()

    def removeToolButton(self, button):
        '''
        @param: button AbstractButtonInterface
        '''
        if not button or button.id() not in self._widgets:
            return

        widget = self._widgets.pop(button.id())
        # TODO: delete
        del widget

    # Q_SLOTS
    def stop(self):
        self._window.action('View/Stop').trigger()

    def reload(self):
        self._window.action('View/Reload').trigger()

    def goBack(self):
        view = self._window.weView()
        view.setFocus()
        view.back()

    def goBackInNewTab(self):
        history = self._window.weView().page().histor()

        if not history.canGoBack():
            return

        self._loadHistoryItemInNewTab(history.backItem())

    def goForward(self):
        view = self._window.weView()
        view.setFocus()
        view.forward()

    def goForwardInNewTab(self):
        history = self._window.weView().page().history()

        if not history.canGoForward():
            return

        self._loadHistoryItemInNewTab(history.forwardItem())

    # private Q_SLOTS
    def _aboutToShowHistoryNextMenu(self):
        if not self._menuForward or not self._window.weView():
            return

        self._menuForward.clear()
        # QWebEngineHistory
        history = self._window.weView().history()

        curindex = history.currentItemIndex()
        count = 0

        for idx in range(curindex+1, history.count()):
            item = history.itemAt(idx)
            if item.isValid():
                title = self.titleForUrl(item.title(), item.url())

                icon = self.iconForPage(item.url(), IconProvider.standardIcon(QStyle.SP_ArrowBack))
                act = Action(icon, title)
                act.setData(idx)
                act.triggered.connect(self._loadHistoryIndex)
                act.ctrlTriggered.connect(self._loadHistoryIndexInNewTab)
                self._menuForward.addAction(act)

            count += 1
            if count == 20:
                break

        self._menuForward.addSeparator()
        self._menuForward.addAction(QIcon.fromTheme('edit-clear'), 'Clear History',
                self._clearHistory)

    def _aboutToShowHistoryBackMenu(self):
        if not self._menuBack or not self._window.weView():
            return

        self._menuBack.clear()
        # QWebEngineHistory
        history = self._window.weView().history()

        curindex = history.currentItemIndex()
        count = 0

        for idx in range(curindex-1, -1, -1):
            item = history.itemAt(idx)
            if item.isValid():
                title = self.titleForUrl(item.title(), item.url())

                icon = self.iconForPage(item.url(), IconProvider.standardIcon(QStyle.SP_ArrowBack))
                act = Action(icon, title)
                act.setData(idx)
                act.triggered.connect(self._loadHistoryIndex)
                act.ctrlTriggered.connect(self._loadHistoryIndexInNewTab)
                self._menuBack.addAction(act)

            count += 1
            if count == 20:
                break

        self._menuBack.addSeparator()
        self._menuBack.addAction(QIcon.fromTheme('edit-clear'), 'Clear History',
                self._clearHistory)

    def _aboutToShowToolsMenu(self):
        self._menuTools.clear()

        self._window.createToolbarsMenu(self._menuTools.addMenu('ToolBars'))
        self._window.createSidebarsMenu(self._menuTools.addMenu('Sidebar'))
        self._menuTools.addSeparator()

        for data in self._widgets.values():
            button = data.button
            if button and (not button.isVisible() or data.id not in self._layoutIds):
                title = button.title()
                if button.badgeText():
                    title += ' (%s)' % button.badgeText()
                act = self._menuTools.addAction(button.icon(), title, self._toolActionActivated)
                act.setData(data.id)

        self._menuTools.addSeparator()
        act = self._menuTools.addAction(IconProvider.settingsIcon(), 'Configure Toolbar',
            self._openConfigurationDialog)
        act.setData(data.id)

    def _loadHistoryIndex(self):
        history = self._window.weView().page().history()

        action = self.sender()
        if isinstance(action, QAction):
            self._loadHistoryItem(history.itemAt(action.data()))

    def _loadHistoryIndexInNewTab(self, index=-1):
        action = self.sender()
        if isinstance(action, QAction):
            index = action.data()

        if index == -1:
            return

        history = self._window.weView().page().history()
        self._loadHistoryItemInNewTab(history.itemAt(index))

    def _clearHistory(self):
        history = self._window.weView().page().history()
        history.clear()

    def _contextMenuRequested(self, pos):
        '''
        @param: pos QPoint
        '''
        menu = QMenu()
        self._window.createToolbarsMenu(menu)
        menu.addSeparator()
        menu.addAction(IconProvider.settingsIcon(), 'Configure Toolbar',
            self._openConfigurationDialog)
        menu.exec_(self.mapToGlobal(pos))

    def _openConfigurationDialog(self):
        dialog = NavigationBarConfigDialog(self)
        dialog.show()

    def _toolActionActivated(self):
        act = self.sender()
        if not isinstance(act, QAction):
            return
        id_ = act.data()
        if id_ not in self._widgets:
            return
        data = self._widgets[id_]
        if not data.button:
            return
        # ToolButton
        buttonTools = self._widgets['button-tools'].widget
        if not buttonTools:
            return

        c = AbstractButtonInterface.ClickController()
        c.visualParent = buttonTools

        def popupPositionFunc(size):
            pos = buttonTools.mapToGlobal(buttonTools.rect().bottomRight())
            if QApplication.isRightToLeft():
                pos.setX(pos.x() - buttonTools.rect().width())
            else:
                pos.setX(pos.x() - size.width())
            c.popupOpened = True
            return pos
        c.popupPosition = popupPositionFunc

        def popupClosedFunc():
            buttonTools.setDown(False)
        c.popupClosed = popupClosedFunc
        data.button.clicked.emit(c)
        if c.popupOpened:
            buttonTools.setDown(True)
        else:
            c.popupClosed()

    # private:
    def _loadSettings(self):
        defaultIds = [
            'button-backforward', 'button-reloadstop', 'button-home',
            'locationbar', 'button-downloads', 'adblock-icon', 'button-tools'
        ]

        settings = Settings()
        settings.beginGroup('NavigationBar')
        self._layoutIds = settings.value('Layout', defaultIds, type=list)
        self._searchLine.setVisible(settings.value('ShowSearchBar', True, type=bool))

        if 'locationbar' not in self._layoutIds:
            self._layoutIds.append('locationbar')

        self._reloadLayout()

    def _reloadLayout(self):
        if not self._widgets:
            return

        self.setUpdatesEnabled(False)

        # Clear layout
        while self._layout.count() != 0:
            # QLayoutItem
            item = self._layout.takeAt(0)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue
            widget.setParent(None)

        # Hide all widgets
        for data in self._widgets.values():
            data.widget.hide()

        # Add widgets to layout
        for id_ in self._layoutIds:
            data = self._widgets.get(id_, None)
            if data and data.widget:
                self._layout.addWidget(data.widget)
                button = data.widget
                if isinstance(data.widget, NavigationBarToolButton):
                    button.updateVisibility()
                else:
                    data.widget.show()

        self._layout.addWidget(self._supMenu)

        # make sure search bar is visible
        if self._searchLine.isVisible() and self._navigationSplitter.sizes()[1] == 0:
            locationBarSize = self._navigationSplitter.sizes()[0]
            self.setSplitterSizes(locationBarSize - 50, 50)

        if self._window.isFullScreen():
            self.enterFullScreen()
        else:
            self.leaveFullScreen()

        self.setUpdatesEnabled(True)

    def _loadHistoryItem(self, item):
        '''
        @param: item QWebEngineHistoryItem
        '''
        history = self._window.weView().page().history()
        history.gotoItem(item)

    def _loadHistoryItemInNewTab(self, item):
        '''
        @param: item QWebEngineHistoryItem
        '''
        tabWidget = self._window.tabWidget()
        tabIndex = tabWidget.duplicateTab(tabWidget.currentIndex())

        history = self._window.weView(tabIndex).page().history()
        history.goToItem(item)

        if gVar.appSettings.newTabPosition == const.NT_SelectedTab:
            tabWidget.setCurrentIndex(tabIndex)
