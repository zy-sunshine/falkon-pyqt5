import re
from sys import stderr
from os import remove
from os.path import join as pathjoin, exists as pathexists
from PyQt5.Qt import Qt
from PyQt5.Qt import QIcon
from PyQt5.Qt import QSqlDatabase
from PyQt5.Qt import QMessageBox
from PyQt5.Qt import QFontDatabase
from PyQt5.Qt import QFont
from PyQt5.Qt import QUrl
from PyQt5.Qt import QSettings
from PyQt5.Qt import QDesktopServices
from PyQt5.Qt import QTimer
from PyQt5.Qt import QByteArray
from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineDownloadItem
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QCoreApplication
from PyQt5.Qt import QThreadPool
from PyQt5.Qt import QProcess
from PyQt5.Qt import QDir
from PyQt5.Qt import QAction
from PyQt5.Qt import QDateTime
from .BrowserWindow import BrowserWindow
from .ProfileManager import ProfileManager
from .Settings import Settings
from .DataPaths import DataPaths
from mc.network.NetworkManager import NetworkManager
from mc.session.SessionManager import SessionManager
from mc.session.RestoreManager import RestoreManager, RestoreData
from mc.tools.AutoSaver import AutoSaver
from mc.autofill.AutoFill import AutoFill
from mc.plugins.PluginProxy import PluginProxy
from mc.other.Updater import Updater
from mc.other.ProtocolHandlerManager import ProtocolHandlerManager
from mc.lib3rd.qtsingleapp.QtSingleApp import QtSingleApp
from mc.common import const
from mc.common.designutil import cached_property
from mc.tools.IconProvider import IconProvider
from mc.history.History import History
from mc.bookmarks.Bookmarks import Bookmarks
from mc.cookies.CookieJar import CookieJar
from mc.downloads.DownloadManager import DownloadManager
from mc.other.UserAgentManager import UserAgentManager
from mc.opensearch.SearchEnginesManager import SearchEnginesManager
from mc.tools.ClosedWindowsManager import ClosedWindowsManager
from mc.tools.html5permissions.HTML5PermissionsManager import HTML5PermissionsManager
from mc.notifications.DesktopNotificationsFactory import DesktopNotificationsFactory
from mc.common.globalvars import gVar
from mc.other.BrowsingLibrary import BrowsingLibrary
from .CommandLineOptions import CommandLineOptions

class MainApplication(QtSingleApp):
    s_testMode = False

    # type AfterLaunch
    OpenBlankPage = 0
    OpenHomePage = 1
    OpenSpeedDial = 2
    RestoreSession = 3
    SelectSession = 4

    def __init__(self, argv):  # noqa 901
        super(MainApplication, self).__init__(argv)
        self._isPrivate = False
        self._isPortable = True
        self._isClosing = False
        self._isStartingAfterCrash = False

        self._history = None  # History
        self._bookmarks = None  # Bookmarks
        self._autoFill = None  # AutoFill
        self._cookieJar = None  # CookieJar
        self._plugins = None  # PluginProxy
        self._browsingLibrary = None  # BrowsingLibrary

        self._networkManager = None
        self._restoreManager = None
        self._sessionManager = None
        self._downloadManager = None
        self._userAgentManager = None
        self._searchEnginesManager = None
        self._closedWindowsManager = None
        self._protocolHandlerManager = None
        self._html5PermissionManager = None
        self._desktopNotifications = None  # DesktopNotificationsFactory
        self._webProfile = None  # QWebEngineProfile

        self._autoSaver = None
        self._proxyStyle = None
        self._wmClass = QByteArray()

        self._windows = []
        self._lastActiveWindow = None
        self._postLaunchActions = []

        self.setAttribute(Qt.AA_UseHighDpiPixmaps)
        self.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

        self.setApplicationName('demo')
        self.setOrganizationDomain('org.autowin')
        self.setWindowIcon(QIcon.fromTheme('demo', QIcon(':/icons/demo.svg')))
        self.setDesktopFileName('orig.autowin.demo')

        self.setApplicationVersion('1.0')

        # Set fallback icon theme (eg. on Windows/Mac)
        if QIcon.fromTheme('view-refresh').isNull():
            QIcon.setThemeName('breeze-fallback')

        # QSQLITE database plugin is required
        if not QSqlDatabase.isDriverAvailable('QSQLITE'):
            QMessageBox.Critical(None, 'Error', 'Qt SQLite database plugin is not available.'
                    ' Please install it and restart the application.')
            self._isClosing = True
            return
        # TODO: Q_OS_WIN
        fontId = QFontDatabase.addApplicationFont('font.ttf')
        if fontId != -1:
            families = QFontDatabase.applicationFontFamilies(fontId)
            if not families.empty():
                self.setFont(QFont(families.at(0)))

        startUrl = QUrl()
        startProfile = ''
        messages = []

        noAddons = False
        newInstance = False

        if len(argv) > 1:
            cmd = CommandLineOptions()
            for pair in cmd.getActions():
                action = pair.action
                text = pair.text
                if action == const.CL_StartWithoutAddons:
                    noAddons = True
                elif action == const.CL_StartWithProfile:
                    startProfile = text
                elif action == const.CL_StartPortable:
                    self._isPortable = True
                elif action == const.CL_NewTab:
                    messages.append("ACTION:NewTab")
                    self._postLaunchActions.append(self.OpenNewTab)
                elif action == const.CL_NewWindow:
                    messages.append("ACTION:NewWindow")
                elif action == const.CL_ToggleFullScreen:
                    messages.append("ACTION:ToggleFullScreen")
                    self._postLaunchActions.append(self.ToggleFullScreen)
                elif action == const.CL_ShowDownloadManager:
                    messages.append("ACTION:ShowDownloadManager")
                    self._postLaunchActions.append(self.OpenDownloadManager)
                elif action == const.CL_StartPrivateBrowsing:
                    self._isPrivate = True
                elif action == const.CL_StartNewInstance:
                    newInstance = True
                elif action == const.CL_OpenUrlInCurrentTab:
                    startUrl = QUrl.fromUserInput(text)
                    messages.append("ACTION:OpenUrlInCurrentTab" + text)
                elif action == const.CL_OpenUrlInNewWindow:
                    startUrl = QUrl.fromUserInput(text)
                    messages.append("ACTION:OpenUrlInNewWindow" + text)
                elif action == const.CL_OpenUrl:
                    startUrl = QUrl.fromUserInput(text)
                    messages.append("URL:" + text)
                elif action == const.CL_ExitAction:
                    self._isClosing = True
                    return
                elif action == const.CL_WMClass:
                    self._wmClass = text

        if not self.isPortable():
            appConf = QSettings(pathjoin(self.applicationDirPath(), '%s.conf' % const.APPNAME), QSettings.IniFormat)
            appConf.value('Config/Portable')

        if self.isPortable():
            print('%s: Running in Portable Mode.' % const.APPNAME)
            DataPaths.setPortableVersion()

        # Don't start single application in private browsing
        if not self.isPrivate():
            appId = 'org.autowin.mc'

            if self.isPortable():
                appId += '.Portable'

            if self.isTestModeEnabled():
                appId += '.TestMode'

            if newInstance:
                if not startProfile or startProfile == 'default':
                    print('New instance cannot be started with default profile!')
                else:
                    # Generate unique appId so it is possible to start more
                    # separate instances of the same profile. It is dangerous to
                    # run more instance of the same profile, but if the user
                    # wants it, we should allow it.
                    appId += '.' + str(QDateTime.currentMSecsSinceEpoch())

            self.setAppId(appId)

        # If there is nothing to tell other instance, we need to at least weak it
        if not messages:
            messages.append(' ')

        if self.isRunning():
            self._isClosing = True
            for message in messages:
                self.sendMessage(message)
            return

        # TODO: Q_OS_MACOS
        #setQuitOnLastWindowClosed(False)
        #disableWindowTabbing()
        self.setQuitOnLastWindowClosed(True)

        QSettings.setDefaultFormat(QSettings.IniFormat)
        QDesktopServices.setUrlHandler('http', self.addNewTab)
        QDesktopServices.setUrlHandler('https', self.addNewTab)
        QDesktopServices.setUrlHandler('ftp', self.addNewTab)

        profileManager = ProfileManager()
        profileManager.initConfigDir()
        profileManager.initCurrentProfile(startProfile)

        Settings.createSettings(pathjoin(DataPaths.currentProfilePath(), 'settings.ini'))

        NetworkManager.registerSchemes()

        if self.isPrivate():
            self._webProfile = QWebEngineProfile()
        else:
            self._webProfile = QWebEngineProfile.defaultProfile()
        self._webProfile.downloadRequested.connect(self.downloadRequested)

        self._networkManager = NetworkManager(self)

        self.setupUserScripts()

        if not self.isPrivate() and not self.isTestModeEnabled():
            self._sessionManager = SessionManager(self)
            self._autoSaver = AutoSaver(self)
            self._autoSaver.save.connect(self._sessionManager.autoSaveLastSession)

            settings = QSettings()
            settings.beginGroup('SessionRestore')
            wasRunning = settings.value('isRunning', False, type=bool)
            wasRestoring = settings.value('isRestoring', False, type=bool)
            settings.setValue('isRunning', True)
            settings.setValue('isRestoring', wasRunning)
            settings.endGroup()
            settings.sync()

            self._isStartingAfterCrash = wasRunning and wasRestoring

            if wasRunning:
                QTimer.singleShot(60 * 1000, lambda: Settings().setValue('SessionRestore/isRestoring', False))

            # we have to ask about startup session before creating main window
            if self._isStartingAfterCrash and self.afterLaunch() == self.SelectSession:
                self._restoreManager = RestoreManager(self.sessionManager().askSessionFromUser())

        self.loadSettings()

        self._plugins = PluginProxy(self)
        self._autoFill = AutoFill(self)
        self.app.protocolHandlerManager()

        if not noAddons:
            self._plugins.loadPlugins()

        window = self.createWindow(const.BW_FirstAppWindow, startUrl)
        window.startingCompleted.connect(self.restoreOverrideCursor)

        self.focusChanged.connect(self.onFocusChanged)

        if not self.isPrivate() and not self.isTestModeEnabled():
            # check updates
            settings = Settings()
            checkUpdates = settings.value('Web-Browser-Settings/CheckUpdates', True, type=bool)

            if checkUpdates:
                Updater(window)

            self.sessionManager().backupSavedSessions()

            if self._isStartingAfterCrash or self.afterLaunch() == self.RestoreSession:
                self._restoreManager = RestoreManager(self.sessionManager().lastActiveSessionPath())
                if not self._restoreManager.isValid():
                    self.destroyRestoreManager()

            if not self._isStartingAfterCrash and self._restoreManager:
                self.restoreSession(window, self._restoreManager.restoreData())

        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, DataPaths.currentProfilePath())

        self.messageReceived.connect(self.messageReceivedCb)
        self.aboutToQuit.connect(self.saveSettings)

        QTimer.singleShot(0, self.postLaunch)

    def __delete__(self):
        self._isClosing = True

        IconProvider.instance().saveIconsToDatabase()

        # Wait for all QtConcurrent jobs to finish
        QThreadPool.globalInstance().waitForDone()

        # Delete all classes that are saving data in destructor
        self._bookmarks = None
        self._cookieJar = None

        Settings.syncSettings()

    @cached_property
    def app(self):
        return MainApplication.instance()

    def isClosing(self):
        return self._isClosing

    def isPrivate(self):
        return self._isPrivate

    def isPortable(self):
        return self._isPortable

    def isStartingAfterCrash(self):
        return self._isStartingAfterCrash

    def windowCount(self):
        return len(self._windows)

    def windows(self):
        '''
        @return: QList<BrowserWindow*>
        '''
        return self._windows

    def getWindow(self):
        '''
        @return: BrowserWindow
        '''
        if self._lastActiveWindow:
            return self._lastActiveWindow
        if not self._windows:
            return None
        else:
            return self._windows[0]

    def createWindow(self, type_, startUrl=QUrl()):
        '''
        @param: type_ const.BrowserWindowType
        @param: startUrl QUrl
        '''
        window = BrowserWindow(type_, startUrl)

        def windowDestroyFunc():
            self.windowDestroyed(window)
        window.destroyed.connect(windowDestroyFunc)

        self._windows.insert(0, window)
        return window

    def afterLaunch(self):
        return Settings().value('Web-URL-Settings/afterLaunch', self.RestoreSession, type=int)

    def openSession(self, window, restoreData):
        '''
        @param: window BrowserWindow*
        @param: restoreData RestoreData
        '''
        self.setOverrideCursor(Qt.BusyCursor)
        if not window:
            window = self.createWindow(None, const.BW_OtherRestoredWindow)
        if window.tabCount() != 0:
            # This can only happend when recovering crashed session!
            # Don't restore tabs in current window as user already opened some
            # new tabs
            window = self.createWindow(None, const.BW_OtherRestoredWindow) \
                .restoreWindow(restoreData.windows.takeAt(0))
        else:
            window.restoreWindow(restoreData.windows.takeAt(0))

        # data -> BrowserWindow::SavedWindow
        for data in restoreData.windows:
            window = self.createWindow(None, const.BW_OtherRestoredWindow)
            window.restoreWindow(data)
        self._closedWindowsManager.restoreState(restoreData.closedWindows)
        self.restoreOverrideCursor()

    def restoreSession(self, window, restoreData):
        if self._isPrivate or not restoreData.isValid():
            return False

        self.openSession(window, restoreData)

        self._restoreManager.clearRestoreData()
        self.destroyRestoreManager()

        return True

    def destroyRestoreManager(self):
        if self._restoreManager and self._restoreManager.isValid():
            return True
        self._restoreManager = None

    def reloadSettings(self):
        self.loadSettings()
        self.settingsReloaded.emit()

    def styleName(self):
        if self._proxyStyle:
            return self._proxyStyle.name()
        else:
            return ''

    def setProxyStyle(self, style):
        '''
        @param: style ProxyStyle
        '''
        self._proxyStyle = style
        self.setStyle(style)

    def wmClass(self):
        return self._wmClass

    def history(self):
        if not self._history:
            self._history = History(self)
        return self._history

    def bookmarks(self):
        if not self._bookmarks:
            self._bookmarks = Bookmarks(self)
        return self._bookmarks

    def autoFill(self):
        return self._autoFill

    def cookieJar(self):
        if not self._cookieJar:
            self._cookieJar = CookieJar(self)
        return self._cookieJar

    def plugins(self):
        return self._plugins

    def browsingLibrary(self):
        if not self._browsingLibrary:
            self._browsingLibrary = BrowsingLibrary(self.getWindow())
        return self._browsingLibrary

    def networkManager(self):
        return self._networkManager

    def restoreManager(self):
        return self._restoreManager

    def sessionManager(self):
        return self._sessionManager

    def downloadManager(self):
        if not self._downloadManager:
            self._downloadManager = DownloadManager()
        return self._downloadManager

    def userAgentManager(self):
        if not self._userAgentManager:
            self._userAgentManager = UserAgentManager()
        return self._userAgentManager

    def searchEnginesManager(self):
        if not self._searchEnginesManager:
            self._searchEnginesManager = SearchEnginesManager()
        return self._searchEnginesManager

    def closedWindowsManager(self):
        if not self._closedWindowsManager:
            self._closedWindowsManager = ClosedWindowsManager()
        return self._closedWindowsManager

    def protocolHandlerManager(self):
        if not self._protocolHandlerManager:
            self._protocolHandlerManager = ProtocolHandlerManager()
        return self._protocolHandlerManager

    def html5PermissionsManager(self):
        if not self._html5PermissionsManager:
            self._html5PermissionsManager = HTML5PermissionsManager()
        return self._html5PermissionsManager

    def desktopNotifications(self):
        if not self._desktopNotifications:
            self._desktopNotifications = DesktopNotificationsFactory(self)
        return self._desktopNotifications

    def webProfile(self):
        return self._webProfile

    def webSettings(self):
        return self._webProfile.settings()

    @classmethod
    def instance(cls):
        return QCoreApplication.instance()

    @classmethod
    def isTestModeEnabled(cls):
        return cls.s_testMode

    @classmethod
    def setTestModeEnabled(cls, enabled):
        cls.s_testMode = enabled

    # Q_SLOTS
    def addNewTab(self, url=QUrl()):
        window = self.getWindow()
        if window:
            window.tabWidget().addView(url, url.isEmpty() and
                const.NT_SelectedNewEmptyTab or const.NT_SelectedTabAtTheEnd)

    def startPrivateBrowsing(self, startUrl=QUrl()):
        url = startUrl
        act = self.sender()
        if isinstance(act, QAction):
            url = QUrl(act.data())
        args = [const.MAIN_PATH]
        args.append('--private-browsing')
        args.append('--profile=%s' % ProfileManager.currentProfile())
        if not url.isEmpty():
            args.append(url.toEncoded().data().decode())
        if not QProcess.startDetached(self.applicationFilePath(), args):
            print('MainApplication: Cannot start new browser process for private browsing!'
                ' %s %s' % (self.applicationFilePath(), args), file=stderr)

    def reloadUserStyleSheet(self):
        userCssFile = Settings().value('Web-Browser-Settings/userStyleSheet', '')
        self.setUserStyleSheet(userCssFile)

    def restoreOverrideCursor(self):
        super().restoreOverrideCursor()

    def changeOccurred(self):
        if self._autoSaver:
            self._autoSaver.changeOccurred()

    def quitApplication(self):
        if self._downloadManager and not self._downloadManager.canClose():
            self._downloadManager.show()
            return
        for window in self._windows:
            window.aboutToClose.emit()
        if self._sessionManager and len(self._windows) > 0:
            self._sessionManager.autoSaveLastSession()
        self._isClosing = True
        for window in self._windows:
            window.close()
        # Saving settings in saveSettings() slot called from quit() so
        # everything gets saved also when quitting application in other
        # way than clicking Quit action in File menu or closing last window
        # eg. on Mac (#157)
        if not self.isPrivate():
            self.removeLockFile()
        self.quit()

    # Q_SIGNALS
    settingsReloaded = pyqtSignal()
    activeWindowChanged = pyqtSignal(BrowserWindow)

    # private Q_SLOTS
    def postLaunch(self):
        if self.OpenDownloadManager in self._postLaunchActions:
            self.downloadManager().show()
        if self.OpenNewTab in self._postLaunchActions:
            self.getWindow().tabWidget().addView(QUrl(), const.NT_SelectedNewEmptyTab)
        if self.ToggleFullScreen in self._postLaunchActions:
            self.getWindow().toggleFullScreen()

        self._createJumpList()
        self._initPulseSupport()

        QTimer.singleShot(5000, self.runDeferredPostLaunchActions)

    def saveState(self):
        restoreData = RestoreData()
        for window in self._windows:
            restoreData.windows.append(BrowserWindow.SavedWindow(window))
        if self._restoreManager and self._restoreManager.isValid():
            stream = QDataStream(restoreData.creashedSession, QIODevice.WriteOnly)
            stream.read(self._restoreManager.restoreData())
        restoreData.closedWindows = self._closedWindowsManager.saveState()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream.read(const.sessionVersion)
        stream.read(restoreData)
        return data

    def saveSettings(self):
        if self.isPrivate():
            return
        self._isClosing = True
        settings = Settings()
        settings.beginGroup('SessionRestore')
        settings.setValue('isRunning', False)
        settings.setValue('sRestoring', False)

        settings.beginGroup('Web-Browser-Settings')
        deleteCache = settings.value('deleteCacheOnClose', False, type=bool)
        deleteHistory = settings.value('deleteHistoryOnClose', False, type=bool)
        deleteHtml5Storage = settings.value('deleteHTML5StorageOnClose', False, type=bool)
        settings.endGroup()

        settings.beginGroup('Cookies-Settings')
        deleteCookies = settings.value('deleteCookiesOnClose', False, type=bool)
        settings.endGroup()

        if deleteHistory:
            self._history.clearHistory()
        if deleteHtml5Storage:
            ClearPrivateData.clearLocalStorage()
        if deleteCookies:
            self._cookieJar.deleteAllCookies(False)
        if deleteCache:
            gVar.appTools.removeRecursively(self.app.webProfile().cachePath())

        if self._searchEnginesManager:
            self._searchEnginesManager.saveSettings()
        self._plugins.shutdown()
        self._networkManager.shutdown()

        gVar.appSettings.saveSettings()
        webpageIconsPath = pathjoin(DataPaths.currentProfilePath(), 'webpageIcons.db')
        if pathexists(webpageIconsPath):
            remove(webpageIconsPath)
        self.sessionManager().saveSettings()

    def messageReceivedCb(self, message):
        '''
        @param: message string
        '''
        actWin = self.getWindow()
        actUrl = QUrl()
        if message.startswith('URL:'):
            url = QUrl.fromUserInput(message[4:])
            self.addNewTab(url)
            actWin = self.getWindow()
        elif message.startswith('ACTION:'):
            text = message[7:]
            if text == 'NewTab':
                self.addNewTab()
            elif text == 'NewWindow':
                actWin = self.createWindow(const.BW_NewWindow)
            elif text == 'ShowDownloadManager':
                self.downloadManager().show()
                actWin = self.downloadManager()
            elif text == 'ToggleFullScreen' and actWin:
                assert(isinstance(actWin, BrowserWindow))
                actWin.toggleFullScreen()
            elif text.startswith('OpenUrlInCurrentTab'):
                actUrl = QUrl.fromUserInput(text[:19])
            elif text.startswith('OpenUrlInNewTab'):
                # user attempted to start another instance. let's open a new one
                self.createWindow(const.BW_NewWindow, QUrl.fromUserInput(text[18:]))
                return
        else:
            actWin = self.createWindow(const.BW_NewWindow)

        if not actWin:
            if not self.isClosing():
                # It can only occur if download manager window was still opened
                self.createWindow(const.BW_NewWindow, actUrl)
            return

        actWin.setWindowState(actWin.windowState() & Qt.WindowMinimized)
        actWin.raise_()
        actWin.activateWindow()
        actWin.setFocus()

        # TODO: convert actWin to BrowserWindow
        win = actWin
        if win and not actWin.isEmpty:
            win.loadAddress(actUrl)

    def windowDestroyed(self, window):
        '''
        @param: message QObject*
        '''
        assert(window)
        assert(window in self._windows)
        self._windows.remove(window)

    def onFocusChanged(self):
        activeBrowserWindow = self.activeWindow()
        if activeBrowserWindow:
            self._lastActiveWindow = activeBrowserWindow
            self.activeWindowChanged.emit(self._lastActiveWindow)

    def runDeferredPostLaunchActions(self):
        self.checkDefaultWebBrowser()
        self.checkOptimizeDatabase()

    def downloadRequested(self, download):
        '''
        @param: download QWebEngineDownloadItem
        '''
        self.downloadManager().download(download)

    # private
    # enum PostLaunchAction
    OpenDownloadManager = 0
    OpenNewTab = 1
    ToggleFullScreen = 2

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Themes')
        activeTheme = settings.value('activeTheme', const.DEFAULT_THEME_NAME)
        settings.endGroup()

        self.loadTheme(activeTheme)

        webSettings = self._webProfile.settings()

        # Web browsing settings
        settings.beginGroup('Web-Browser-Settings')

        webSettings.setAttribute(QWebEngineSettings.LocalStorageEnabled,
                settings.value("HTML5StorageEnabled", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.PluginsEnabled,
                settings.value("allowPlugins", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.JavascriptEnabled,
                settings.value("allowJavaScript", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows,
                settings.value("allowJavaScriptOpenWindow", False, type=bool))
        webSettings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard,
                settings.value("allowJavaScriptAccessClipboard", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.LinksIncludedInFocusChain,
                settings.value("IncludeLinkInFocusChain", False, type=bool))
        webSettings.setAttribute(QWebEngineSettings.XSSAuditingEnabled,
                settings.value("XSSAuditing", False, type=bool))
        webSettings.setAttribute(QWebEngineSettings.PrintElementBackgrounds,
                settings.value("PrintElementBackground", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.SpatialNavigationEnabled,
                settings.value("SpatialNavigation", False, type=bool))
        webSettings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled,
                settings.value("AnimateScrolling", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        webSettings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        webSettings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        webSettings.setAttribute(QWebEngineSettings.FocusOnNavigationEnabled, False)

        webSettings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript,
                settings.value("allowJavaScriptActivationWindow", False, type=bool))

        webSettings.setAttribute(QWebEngineSettings.JavascriptCanPaste,
                settings.value("allowJavaScriptPaste", True, type=bool))
        webSettings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture,
                settings.value("DisableVideoAutoPlay", False, type=bool))
        webSettings.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly,
                settings.value("WebRTCPublicIpOnly", True, type=bool))
        webSettings.setUnknownUrlSchemePolicy(QWebEngineSettings.AllowAllUnknownUrlSchemes)

        webSettings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled,
                settings.value("DNSPrefetch", True, type=bool))

        webSettings.setDefaultTextEncoding(settings.value("DefaultEncoding",
            webSettings.defaultTextEncoding(), type=str))

        self.setWheelScrollLines(settings.value("wheelScrollLines", self.wheelScrollLines(), type=int))

        userCss = settings.value("userStyleSheet", '', type=str)
        settings.endGroup()

        self.setUserStyleSheet(userCss)

        settings.beginGroup("Browser-Fonts")
        webSettings.setFontFamily(QWebEngineSettings.StandardFont,
                settings.value("StandardFont", webSettings.fontFamily(
                    QWebEngineSettings.StandardFont), type=str))
        webSettings.setFontFamily(QWebEngineSettings.CursiveFont,
                settings.value("CursiveFont", webSettings.fontFamily(
                    QWebEngineSettings.CursiveFont), type=str))
        webSettings.setFontFamily(QWebEngineSettings.FantasyFont,
                settings.value("FantasyFont", webSettings.fontFamily(
                    QWebEngineSettings.FantasyFont), type=str))
        webSettings.setFontFamily(QWebEngineSettings.FixedFont,
                settings.value("FixedFont", webSettings.fontFamily(
                    QWebEngineSettings.FixedFont), type=str))
        webSettings.setFontFamily(QWebEngineSettings.SansSerifFont,
                settings.value("SansSerifFont", webSettings.fontFamily(
                    QWebEngineSettings.SansSerifFont), type=str))
        webSettings.setFontFamily(QWebEngineSettings.SerifFont,
                settings.value("SerifFont", webSettings.fontFamily(
                    QWebEngineSettings.SerifFont), type=str))
        webSettings.setFontSize(QWebEngineSettings.DefaultFontSize,
                settings.value("DefaultFontSize", 15, type=int))
        webSettings.setFontSize(QWebEngineSettings.DefaultFixedFontSize,
                settings.value("FixedFontSize", 14, type=int))
        webSettings.setFontSize(QWebEngineSettings.MinimumFontSize,
                settings.value("MinimumFontSize", 3, type=int))
        webSettings.setFontSize(QWebEngineSettings.MinimumLogicalFontSize,
                settings.value("MinimumLogicalFontSize", 5, type=int))
        settings.endGroup()

        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        profile.setPersistentStoragePath(DataPaths.currentProfilePath())

        defaultPath = DataPaths.path(DataPaths.Cache)
        if not defaultPath.startswith(DataPaths.currentProfilePath()):
            defaultPath += '/' + ProfileManager.currentProfile()
        cachePath = settings.value("Web-Browser-Settings/CachePath", defaultPath, type=str)
        profile.setCachePath(cachePath)

        allowCache = settings.value("Web-Browser-Settings/AllowLocalCache", True, type=bool)
        profile.setHttpCacheType(allowCache and QWebEngineProfile.DiskHttpCache or QWebEngineProfile.MemoryHttpCache)

        cacheSize = settings.value("Web-Browser-Settings/LocalCacheSize", 50, type=int) * 1000 * 1000
        profile.setHttpCacheMaximumSize(cacheSize)

        settings.beginGroup("SpellCheck")
        profile.setSpellCheckEnabled(settings.value("Enabled", False, type=bool))
        profile.setSpellCheckLanguages(settings.value("Languages", type=list))
        settings.endGroup()

        if self.isPrivate():
            webSettings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
            self.history().setSaving(False)

        if self._downloadManager:
            self._downloadManager.loadSettings()

        gVar.appSettings.loadSettings()
        self.userAgentManager().loadSettings()
        self.networkManager().loadSettings()

    def loadTheme(self, name):
        activeThemePath = DataPaths.locate(DataPaths.Themes, name)

        if not activeThemePath:
            print('Warning: Cannot load theme %s' % name)
            activeThemePath = '%s/%s' % (DataPaths.path(DataPaths.Themes), const.DEFAULT_THEME_NAME)

        qss = gVar.appTools.readAllFileContents(activeThemePath + '/main.css')

        if const.OS_MACOS:
            qss += gVar.appTools.readAllFileContents(activeThemePath + '/mac.css')
        elif const.OS_UNIX:
            qss += gVar.appTools.readAllFileContents(activeThemePath + '/linux.css')
        elif const.OS_WIN:
            qss += gVar.appTools.readAllFileContents(activeThemePath + '/windows.css')

        if self.isRightToLeft():
            qss += gVar.appTools.readAllFileContents(activeThemePath + 'rtl.css')

        if self.isPrivate():
            qss += gVar.appTools.readAllFileContents(activeThemePath + 'private.css')

        qss += gVar.appTools.readAllFileContents(activeThemePath + 'userChrome.css')

        relativePath = QDir.current().relativeFilePath(activeThemePath)
        qss = re.sub("url\\s*\\(\\s*([^\\*:\\);]+)\\s*\\)", r'url(' + relativePath + r'/\1)', qss)
        self.setStyleSheet(qss)

    def setupUserScripts(self):
        pass

    def setUserStyleSheet(self, filePath):
        pass

    def checkDefaultWebBrowser(self):
        pass

    def checkOptimizeDatabase(self):
        pass

    # private:
    def _createJumpList(self):
        pass

    def _initPulseSupport(self):
        pass
