from PyQt5.QtWidgets import QMenu
from mc.common.globalvars import gVar
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QAction
from PyQt5.Qt import QIcon
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import Qt
from mc.webengine.WebInspector import WebInspector
from mc.common import const
from PyQt5.Qt import QUrl
from PyQt5.Qt import QDesktopServices
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.history.HistoryMenu import HistoryMenu
from mc.bookmarks.BookmarksMenu import BookmarksMenu
from mc.other.SiteInfo import SiteInfo
from mc.other.AboutDialog import AboutDialog
from mc.preferences.Preferences import Preferences

class MainMenu(QMenu):
    def __init__(self, window, parent=None):
        super(MainMenu, self).__init__(parent)
        self._actions = {}  # QHash<QString, QAction>
        self._window = window   # QPointer<BrowserWindow>
        self._preferences = None  # QPointer<Preferences>

        self._menuFile = None  # QMenu
        self._menuEdit = None  # QMenu
        self._menuView = None  # QMenu
        self._menuTools = None # QMenu
        self._menuHelp = None  # QMenu
        self._submenuExtensions = None  # QMenu
        self._menuHistory = None  # HistoryMenu
        self._menuBookmarks = None  # BookmarksMenu
        assert(self._window)
        self._init()

    def initMenuBar(self, menuBar):
        '''
        @param: menuBar QMenuBar
        '''
        menuBar.addMenu(self._menuFile)
        menuBar.addMenu(self._menuEdit)
        menuBar.addMenu(self._menuView)
        menuBar.addMenu(self._menuHistory)
        menuBar.addMenu(self._menuBookmarks)
        menuBar.addMenu(self._menuTools)
        menuBar.addMenu(self._menuHelp)

    def initSuperMenu(self, superMenu):
        '''
        @param: superMenu QMenu
        '''
        superMenu.addAction(self._actions['File/NewTab'])
        superMenu.addAction(self._actions['File/NewWindow'])
        superMenu.addAction(self._actions['File/NewPrivateWindow'])
        superMenu.addAction(self._actions['File/OpenFile'])
        sessionManager = gVar.app.sessionManager()
        if sessionManager:
            superMenu.addSeparator()
            sessionsSubmenu = QMenu('Sessions')
            sessionsSubmenu.aboutToShow.connect(
                sessionManager._aboutToShowSessionsMenu
            )
            superMenu.addMenu(sessionsSubmenu)
            superMenu.addAction(self._actions['File/SessionManager'])

        superMenu.addSeparator()
        superMenu.addAction(self._actions['File/SendLink'])
        superMenu.addAction(self._actions['File/Print'])
        superMenu.addSeparator()
        superMenu.addAction(self._actions['Edit/SelectAll'])
        superMenu.addAction(self._actions['Edit/Find'])
        superMenu.addSeparator()
        superMenu.addAction(self._menuHistory.actions()[3])
        superMenu.addAction(self._menuBookmarks.actions()[2])
        superMenu.addSeparator()
        superMenu.addMenu(self._menuView)
        superMenu.addMenu(self._menuHistory)
        superMenu.addMenu(self._menuBookmarks)
        superMenu.addMenu(self._menuTools)
        superMenu.addMenu(self._menuHelp)
        superMenu.addSeparator()
        superMenu.addAction(self._actions['Standard/Preferences'])
        superMenu.addAction(self._actions['Standard/About'])
        superMenu.addSeparator()
        superMenu.addAction(self._actions['Standard/Quit'])

    def action(self, name):
        '''
        @param: name QString
        @return: QAction
        '''
        result = self._actions[name]
        assert(result)
        return result

    # Q_SLOTS
    def setWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        assert(window)
        self._window = window
        self._addActionsToWindow()

    # private Q_SLOTS
    # Standard actions
    def _showAboutDialog(self):
        dialog = AboutDialog(self._window)
        dialog.open()

    def _showPreferences(self):
        if not self._preferences:
            self._preferences = Preferences(self._window)

            def destroyFunc():
                self._preferences = None
            self._preferences.destroyed.connect(destroyFunc)

        self._preferences.show()
        self._preferences.raise_()
        self._preferences.activateWindow()

    def _quitApplication(self):
        gVar.app.quitApplication()

    # File menu
    def _newTab(self):
        self._callSlot('addTab')

    def _newWindow(self):
        gVar.app.createWindow(const.BW_NewWindow)

    def _newPrivateWindow(self):
        gVar.app.startPrivateBrowsing()

    def _openLocation(self):
        self._callSlot('_openLocation')

    def _openFile(self):
        self._callSlot('_openFile')

    def _closeWindow(self):
        self._callSlot('_closeWindow')

    def _savePageAs(self):
        if self._window:
            func = getattr(self._window.weView(), 'savePageAs')
            func()

    def _sendLink(self):
        mainUrl = QUrl.fromEncoded('mailto:%20?body=' +
            QUrl.toPercentEncoding(self._window.weView.url().toEncoded()) +
            '&subject=' + QUrl.toPercentEncoding(self._window.weView.title()))
        QDesktopServices.openUrl(mainUrl)

    def _printPage(self):
        self._callSlot('printPage')

    # Edit menu
    def _editUndo(self):
        if self._window:
            self._window.weView().editUndo()

    def _editRedo(self):
        if self._window:
            self._window.weView().editRedo()

    def _editCut(self):
        if self._window:
            self._window.weView().editCut()

    def _editCopy(self):
        if self._window:
            self._window.weView().editCopy()

    def _editPaste(self):
        if self._window:
            self._window.weView().editPaste()

    def _editSelectAll(self):
        if self._window:
            self._window.weView().editSelectAll()

    def _editFind(self):
        self._callSlot('searchOnPage')

    # View menu
    def _showStatusBar(self):
        if self._window:
            self._window.toggleShowStatusBar()

    def _stop(self):
        if self._window:
            self._window.weView().stop()

    def _reload(self):
        if self._window:
            self._window.weView().reload()

    def _zoomIn(self):
        if self._window:
            self._window.weView().zoomIn()

    def _zoomOut(self):
        if self._window:
            self._window.weView().zoomOut()

    def _zoomReset(self):
        if self._window:
            self._window.weView().zoomReset()

    def _showPageSource(self):
        self._callSlot('showSource')

    def _showFullScreen(self):
        if self._window:
            self._window.toggleFullScreen()

    # Tools menu
    def _webSearch(self):
        self._callSlot('webSearch')

    def _showSiteInfo(self):
        if self._window and SiteInfo.canShowSiteInfo(self._window.weView().url()):
            info = SiteInfo(self._window.weView())
            info.show()

    def _showDownloadManager(self):
        m = gVar.app.downloadManager()
        m.show()
        m.raise_()

    def _showCookieManager(self):
        m = CookieManager(self._window)
        m.show()
        m.raise_()

    def _toggleWebInspector(self):
        self._callSlot('toggleWebInspector')

    def _showClearRecentHistoryDialog(self):
        # ClearPrivateData
        dialog = ClearPrivateData(self._window)
        dialog.open()

    # Help menu
    def _aboutQt(self):
        QApplication.aboutQt()

    def _showInfoAboutApp(self):
        if self._window:
            self._window.tabWidget().addViewByUrl(QUrl('app:about'), const.NT_CleanSelectedTab)

    def _showConfigInfo(self):
        if self._window:
            self._window.tabWidget().addViewByUrl(QUrl('app:config'), const.NT_CleanSelectedTab)

    def _reportIssue(self):
        if self._window:
            self._window.tabWidget().addViewByUrl(QUrl('app:reportbug'), const.NT_CleanSelectedTab)

    # Other actions
    def _restoreClosedTab(self):
        if self._window:
            self._window.tabWidget().restoreClosedTab()

    def _aboutToShowFileMenu(self):
        if not const.OS_MACOS:
            self._actions['File/CloseWindow'].setEnabled(gVar.app.windowCount() > 1)

    def _aboutToShowViewMenu(self):
        if not self._window:
            return

        self._actions['View/ShowStatusBar'].setChecked(self._window.statusBar().isVisible())
        self._actions['View/FullScreen'].setChecked(self._window.isFullScreen())

    def _aboutToShowEditMenu(self):
        if not self._window:
            return

        view = self._window.weView()

        self._actions['Edit/Undo'].setEnabled(
            view.pageAction(QWebEnginePage.Undo).isEnabled()
        )
        self._actions['Edit/Redo'].setEnabled(
            view.pageAction(QWebEnginePage.Redo).isEnabled()
        )
        self._actions['Edit/Cut'].setEnabled(
            view.pageAction(QWebEnginePage.Cut).isEnabled()
        )
        self._actions['Edit/Copy'].setEnabled(
            view.pageAction(QWebEnginePage.Copy).isEnabled()
        )
        self._actions['Edit/Paste'].setEnabled(
            view.pageAction(QWebEnginePage.Paste).isEnabled()
        )
        self._actions['Edit/SelectAll'].setEnabled(
            view.pageAction(QWebEnginePage.SelectAll).isEnabled()
        )

    def _aboutToShowToolsMenu(self):
        if not self.window:
            return

        self._actions['Tools/SiteInfo'].setEnabled(SiteInfo.canShowSiteInfo(
            self._window.weView().url()
        ))

        self._submenuExtensions.clear()
        gVar.app.plugins().populateExtensionsMenu(self._submenuExtensions)

        self._submenuExtensions.menuAction().setVisible(not self._submenuExtensions.actions())

    def _aboutToShowSuperMenu(self):
        if not self._window:
            return

        view = self._window.weView()

        self._actions['Edit/Find'].setEnabled(True)
        self._actions['Edit/SelectAll'].setEnabled(view.pageAction(QWebEnginePage.SelectAll).isEnabled())

    def _aboutToShowtoolbarsMenu(self):
        menu = self.sender()
        assert(isinstance(menu, QMenu))

        if self._window:
            menu.clear()
            self._window.createToolbarsMenu(menu)

    def _aboutToShowSidebarsMenu(self):
        menu = self.sender()
        assert(isinstance(menu, QMenu))

        if self._window:
            self._window.createSidebarsMenu(menu)

    def _aboutToShowEncodingMenu(self):
        menu = self.sender()
        assert(isinstance(menu, QMenu))

        if self._window:
            menu.clear()
            self._window.createEncodingMenu(menu)

    # private:
    def _init(self):
        # Standard actions - needed on Mac to be placed correctly in
        # "application" menu
        action = QAction(QIcon.fromTheme('help-about'), '&About App', self)
        action.setMenuRole(QAction.AboutRole)
        action.triggered.connect(self._showAboutDialog)
        self._actions['Standard/About'] = action

        action = QAction(IconProvider.settingsIcon(), 'Pr&eferences', self)
        action.setMenuRole(QAction.PreferencesRole)
        action.setShortcut(QKeySequence(QKeySequence.Preferences))
        action.triggered.connect(self._showPreferences)
        self._actions['Standard/Preferences'] = action

        action = QAction(QIcon.fromTheme('application-exit'), 'Quit', self)
        action.setMenuRole(QAction.QuitRole)
        # Shortcut set from browserWindow
        action.triggered.connect(self._quitApplication)
        self._actions['Standard/Quit'] = action

        # File menu
        self._menuFile = QMenu('&File')
        self._menuFile.aboutToShow.connect(self._aboutToShowFileMenu)

        self._ADD_ACTION('File/NewTab', self._menuFile, IconProvider.newTabIcon(),
            'New Tab', self._newTab, 'Ctrl+T')
        self._ADD_ACTION('File/NewWindow', self._menuFile, IconProvider.newWindowIcon(),
            '&New Window', self._newWindow, 'Ctrl+N')
        self._ADD_ACTION('File/NewPrivateWindow', self._menuFile, IconProvider.privateBrowsingIcon(),
            'New &Private Window', self._newPrivateWindow, 'Ctrl+Shift+P')
        self._ADD_ACTION('File/OpenLocation', self._menuFile, QIcon.fromTheme('document-open-remote'),
            'Open Location', self._openLocation, 'Ctrl+L')
        self._ADD_ACTION('File/OpenFile', self._menuFile, QIcon.fromTheme('document-open'),
            'Open &File...', self._openFile, 'Ctrl+O')
        self._ADD_ACTION('File/CloseWindow', self._menuFile, QIcon.fromTheme('window-close'),
            'Close Window', self._closeWindow, 'Ctrl+Shift+W')
        self._menuFile.addSeparator()

        sessionManager = gVar.app.sessionManager()
        if sessionManager:
            sessionsSubmenu = QMenu('Sessions')
            sessionsSubmenu.aboutToShow.connect(sessionManager._aboutToShowSessionsMenu)
            self._menuFile.addMenu(sessionsSubmenu)
            action = QAction('Session Manager', self)
            action.triggered.connect(sessionManager.openSessionManagerDialog)
            self._actions['File/SessionManager'] = action
            self._menuFile.addAction(action)
            self._menuFile.addSeparator()

        self._ADD_ACTION('File/SavePageAs', self._menuFile, QIcon.fromTheme('document-save'),
            '&Save Page As...', self._savePageAs, 'Ctrl+S')
        self._ADD_ACTION('File/SendLink', self._menuFile, QIcon.fromTheme('mail-message-new'),
            'Send Link...', self._sendLink, '')
        self._ADD_ACTION('File/Print', self._menuFile, QIcon.fromTheme('document-print'),
            '&Print...', self._printPage, 'Ctrl+P')
        self._menuFile.addSeparator()
        self._menuFile.addAction(self._actions['Standard/Quit'])

        # Edit Menu
        self._menuEdit = QMenu('&Edit')
        self._menuEdit.aboutToShow.connect(self._aboutToShowEditMenu)

        action = self._ADD_ACTION('Edit/Undo', self._menuEdit, QIcon.fromTheme('edit-undo'),
            '&Undo', self._editUndo, 'Ctrl+Z')
        action.setShortcutContext(Qt.WidgetShortcut)
        action = self._ADD_ACTION('Edit/Redo', self._menuEdit, QIcon.fromTheme('edit-redo'),
            '&Redo', self._editRedo, 'Ctrl+Shift+Z')
        action.setShortcutContext(Qt.WidgetShortcut)
        self._menuEdit.addSeparator()
        action = self._ADD_ACTION('Edit/Cut', self._menuEdit, QIcon.fromTheme('edit-cut'),
            '&Cut', self._editCut, 'Ctrl+X')
        action.setShortcutContext(Qt.WidgetShortcut)
        action = self._ADD_ACTION('Edit/Copy', self._menuEdit, QIcon.fromTheme('edit-copy'),
            'C&opy', self._editCopy, 'Ctrl+C')
        action.setShortcutContext(Qt.WidgetShortcut)
        action = self._ADD_ACTION('Edit/Paste', self._menuEdit, QIcon.fromTheme('edit-paste'),
            '&Paste', self._editPaste, 'Ctrl+V')
        action.setShortcutContext(Qt.WidgetShortcut)
        self._menuEdit.addSeparator()
        action = self._ADD_ACTION('Edit/SelectAll', self._menuEdit, QIcon.fromTheme('edit-select-all'),
            'Select &All', self._editSelectAll, 'Ctrl+A')
        action.setShortcutContext(Qt.WidgetShortcut)
        action = self._ADD_ACTION('Edit/Find', self._menuEdit, QIcon.fromTheme('edit-find'),
            '&Find', self._editFind, 'Ctrl+F')
        action.setShortcutContext(Qt.WidgetShortcut)
        self._menuFile.addSeparator()

        # View menu
        self._menuView = QMenu('&View')
        self._menuView.aboutToShow.connect(self._aboutToShowViewMenu)

        toolbarsMenu = QMenu('Toolbars', self._menuView)
        toolbarsMenu.aboutToShow.connect(self._aboutToShowtoolbarsMenu)
        sidebarMenu = QMenu('Sidebar', self._menuView)
        sidebarMenu.aboutToShow.connect(self._aboutToShowSidebarsMenu)
        encodingMenu = QMenu('Character &Encoding', self._menuView)
        encodingMenu.aboutToShow.connect(self._aboutToShowEncodingMenu)

        # Create menus to make shortcuts available event before first showing
        # the menu
        self._window.createToolbarsMenu(toolbarsMenu)
        self._window.createSidebarsMenu(sidebarMenu)

        self._menuView.addMenu(toolbarsMenu)
        self._menuView.addMenu(sidebarMenu)
        self._ADD_CHECKABLE_ACTION('View/ShowStatusBar', self._menuView, QIcon(),
            'Sta&tus Bar', self._showStatusBar, '')
        self._menuView.addSeparator()
        self._ADD_ACTION('View/Stop', self._menuView, QIcon.fromTheme('process-stop'),
            '&Stop', self._stop, 'Esc')
        self._ADD_ACTION('View/Reload', self._menuView, QIcon.fromTheme('view-refresh'),
            '&Reload', self._reload, 'F5')
        self._menuView.addSeparator()
        self._ADD_ACTION('View/ZoomIn', self._menuView, QIcon.fromTheme('zoom-in'),
            'Zoom &In', self._zoomIn, 'Ctrl++')
        self._ADD_ACTION('View/ZoomOut', self._menuView, QIcon.fromTheme('zoom-out'),
            'Zoom &Out', self._zoomOut, 'Ctrl+-')
        self._ADD_ACTION('View/ZoomReset', self._menuView, QIcon.fromTheme('zoom-original'),
            'Reset', self._zoomReset, 'Ctrl+0')
        self._menuView.addSeparator()
        self._menuView.addMenu(encodingMenu)
        self._menuView.addSeparator()
        action = self._ADD_ACTION('View/PageSource', self._menuView, QIcon.fromTheme('text-html'),
            '&Page Source', self._showPageSource, 'Ctrl+U')
        action.setShortcutContext(Qt.WidgetShortcut)
        self._ADD_CHECKABLE_ACTION('View/FullScreen', self._menuView, QIcon.fromTheme('view-fullscreen'),
            '&FullScreen', self._showFullScreen, 'F11')

        # Tool menu
        self._menuTools = QMenu('&Tools')
        self._menuTools.aboutToShow.connect(self._aboutToShowToolsMenu)

        self._ADD_ACTION('Tools/WebSearch', self._menuTools, QIcon.fromTheme('edit-find'),
            '&Web Search', self._webSearch, 'Ctrl+K')
        action = self._ADD_ACTION('Tools/SiteInfo', self._menuTools, QIcon.fromTheme('dialog-information'),
            'Site &Info', self._showSiteInfo, 'Ctrl+I')
        action.setShortcutContext(Qt.WidgetShortcut)
        self._menuTools.addSeparator()
        self._ADD_ACTION('Tools/DownloadManager', self._menuTools, QIcon.fromTheme('download'),
            '&Download Manager', self._showDownloadManager, 'Ctrl+Y')
        self._ADD_ACTION('Tools/CookiesManager', self._menuTools, QIcon(),
            '&Cookies Manager', self._showCookieManager, '')
        self._ADD_ACTION('Tools/WebInspector', self._menuTools, QIcon(),
            'Web In&spector', self._toggleWebInspector, 'Ctrl+Shift+I')
        self._ADD_ACTION('Tools/ClearRecentHistory', self._menuTools, QIcon.fromTheme('edit-clear'),
            'Clear Recent &History', self._showClearRecentHistoryDialog, 'Ctrl+Shift+Del')

        if not WebInspector.isEnabled():
            self._actions['Tools/WebInspector'].setVisible(False)

        self._submenuExtensions = QMenu('&Extensions')
        self._submenuExtensions.menuAction().setVisible(False)
        self._menuTools.addMenu(self._submenuExtensions)
        self._menuTools.addSeparator()

        # Help menu
        self._menuHelp = QMenu('&Help')

        # ifndef Q_OS_MACOS
        self._ADD_ACTION('Help/AboutQt', self._menuHelp, QIcon(),
            'About &Qt', self._aboutQt, '')
        self._menuHelp.addAction(self._actions['Standard/About'])
        self._menuHelp.addSeparator()
        # endif

        self._ADD_ACTION('Help/InfoAboutApp', self._menuHelp, QIcon.fromTheme('help-contents'),
            'Information about application', self._showInfoAboutApp, '')
        self._ADD_ACTION('Help/ConfigInfo', self._menuHelp, QIcon(),
            'Configuration Information', self._showConfigInfo, '')
        self._ADD_ACTION('Help/ReportIssue', self._menuHelp, QIcon(),
            'Report &Issue', self._reportIssue, '')

        self._actions['Help/InfoAboutApp'].setShortcut(QKeySequence(QKeySequence.HelpContents))

        # History menu
        self._menuHistory = HistoryMenu()
        self._menuHistory.setMainWindow(self._window)

        # Bookmarks menu
        self._menuBookmarks = BookmarksMenu()
        self._menuBookmarks.setMainWindow(self._window)

        # Other actions
        action = QAction(QIcon.fromTheme('user-trash'),
            'Restore &Closed Tab', self)
        action.setShortcut(QKeySequence('Ctrl+Shift+T'))
        action.triggered.connect(self._restoreClosedTab)
        self._actions['Other/RestoreClosedTab'] = action

        # # ifdef Q_OS_MACOS
        # self._actions['View/FullScreen'].setShortcut(QKeySequence('Ctrl+Meta+F'))
        # # Add standard actions to File Menu (as it won't be ever cleared) and
        # # Mac menubar should move them to "Application" menu
        # self._menuFile.addAction(self._actions['Standard/About'])
        # self._menuFile.addAction(self._actions['Standard/Preferences'])

        # # Prevent ConfigInfo action to be detected as "Preferences..." action in
        # # Mac
        # self._actions['Help/ConfigInfo'].setMenuRole(QAction.NoRole)

        # # Create Dock Menu
        # dockMenu = QMenu(0)
        # dockMenu.addAction(self._actions['File/NewTab'])
        # dockMenu.addAction(self._actions['File/NewWindow'])
        # dockMenu.addAction(self._actions['File/NewPrivateWindow'])
        # qt_mac_set_dock_menu(dockMenu)
        # # endif

        if const.OS_UNIX and not const.OS_MACOS:
            self._menuEdit.addAction(self._actions['Standard/Preferences'])
        elif not const.OS_MACOS:
            self._menuTools.addAction(self._actions['Standard/Preferences'])

        self._addActionsToWindow()

    def _ADD_ACTION(self, name, menu, icon, trName, slot, shortcut):
        action = menu.addAction(icon, trName)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        self._actions[name] = action
        return action

    def _ADD_CHECKABLE_ACTION(self, name, menu, icon, trName, slot, shortcut):
        action = menu.addAction(icon, trName)
        action.setShortcut(QKeySequence(shortcut))
        action.setCheckable(True)
        action.triggered.connect(slot)
        self._actions[name] = action
        return action

    def _addActionsToWindow(self):
        '''
        @brief: Make shortcuts available even in fullscreen (hidden menu)
        '''
        actions = []  # QList<QAction*>
        actions.extend(self._menuFile.actions())
        actions.extend(self._menuEdit.actions())
        actions.extend(self._menuView.actions())
        actions.extend(self._menuTools.actions())
        actions.extend(self._menuHelp.actions())
        actions.extend(self._menuHistory.actions())
        actions.extend(self._menuBookmarks.actions())
        actions.append(self._actions['Other/RestoreClosedTab'])

        for action in actions:
            if action.menu():
                actions.extend(action.menu().actions())
            self._window.addAction(action)

    def _callSlot(self, slot):
        '''
        @param: slot const char*
        '''
        if self._window:
            getattr(self._window, slot)()
