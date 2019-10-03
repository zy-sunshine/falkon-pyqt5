from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineScript
from PyQt5.QtWebEngineCore import QWebEngineRegisterProtocolHandlerRequest
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from PyQt5.Qt import QTime
from PyQt5.Qt import QPointF
from PyQt5.Qt import QWebChannel
from PyQt5.Qt import QEventLoop
from mc.common.globalvars import gVar
from PyQt5.Qt import QUrlQuery
from PyQt5.Qt import QDir
from mc.common import const
from PyQt5.Qt import QTimer
from .javascript.ExternalJsObject import ExternalJsObject
from mc.tools.Scripts import Scripts
from PyQt5.Qt import QFileInfo, QFile
from mc.tools.DelayedFileWatcher import DelayedFileWatcher
from .WebHitTestResult import WebHitTestResult

class WebPage(QWebEnginePage):
    # JsWorld
    UnsafeJsWorld = QWebEngineScript.MainWorld
    SafeJsWorld = QWebEngineScript.ApplicationWorld

    # static members
    s_lastUploadLocation = ''
    s_lastUnsupportedUrl = ''
    s_lastUnsupportedUrlTime = QTime()

    # private members
    _s_lastUploadLocation = QDir.homePath()
    _s_supportedSchemes = []  # QStringList
    def __init__(self, parent=None):
        super(WebPage, self).__init__(parent)
        self._fileWatcher = None  # DelayedFileWatcher
        self._runningLoop = None  # QEventLoop

        self._autoFillUsernames = []  # QStringList
        # QWebEngineRegisterProtocolHandlerRequest
        self._registerProtocolHandlerRequest = None

        self._loadProgress = 0
        self._blockAlerts = False
        self._secureStatus = False

        self._contentsResizedConnection = None # QMetaObject::Connection

        channel = QWebChannel(self)
        ExternalJsObject.setupWebChannel(channel, self)
        self.setWebChannel(channel, self.SafeJsWorld)

        self.loadProgress.connect(self._progress)
        self.loadFinished.connect(self._finished)
        self.urlChanged.connect(self._urlChanged)
        self.featurePermissionRequested.connect(self._featurePermissionRequested)
        self.windowCloseRequested.connect(self._windowCloseRequested)
        self.fullScreenRequested.connect(self._fullScreenRequested)
        self.renderProcessTerminated.connect(self._renderProcessTerminated)

        def authFunc(url, auth, proxyHost):
            '''
            @param: url QUrl
            @param: auth QAuthenticator
            @param: proxyHost QString
            '''
            gVar.app.networkManager().proxyAuthentication(proxyHost, auth, self.view())
        self.authenticationRequired.connect(authFunc)

        # Workaround QWebEnginePage not scrolling to anchors when opened in
        # background tab
        def contentsResizeFunc():
            # QString
            fragment = self.url().fragment()
            if fragment:
                self.runJavaScript(Scripts.scrollToAnchor(fragment))
            self.contentsSizeChanged.disconnect(self._contentsResizedConnection)
        self._contentsResizedConnection = self.contentsSizeChanged.connect(contentsResizeFunc)

        # Workaround for broken load started/finished signals in QWebEngine 5.10 5.11
        # NOTE: if open this revise, will cause page and view loadFinished emit
        # multi time
        #def loadProgressFunc(progress):
        #    '''
        #    @param: progress int
        #    '''
        #    if progress == 100:
        #        self.loadFinished.emit(True)
        #self.loadProgress.connect(loadProgressFunc)

        # if QTWEBENGINEWIDGETS_VERSION >= QT_VERSION_CHECK(5, 11, 0)
        def registerProtocolHandlerFunc(request):
            '''
            @param: request QWebEngineRegisterProtocolHandlerRequest
            '''
            del self._registerProtocolHandlerRequest
            self._registerProtocolHandlerRequest = QWebEngineRegisterProtocolHandlerRequest(request)
        self.registerProtocolHandlerRequested.connect(registerProtocolHandlerFunc)

        # QTWEBENGINEWIDGETS_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        super().printRequested.connect(self.printRequested)

        def selectClientCertFunc(selection):
            '''
            @param: selection QWebEngineClientCertificateSelection
            '''
            # TODO: It should prompt user, and Falkon does not support yet.
            selection.select(selection.certificates()[0])
        self.selectClientCertificate.connect(selectClientCertFunc)

    def view(self):
        '''
        @return: WebView
        '''
        # TODO: return static_cast<WebView*>(QWebEnginePage::view())
        return super().view()

    def execPrintPage(self, printer, timeout=1000):
        '''
        @param: pointer QPointer
        @param: timeout int
        '''

    def execJavaScript(self, scriptSource, worldId=UnsafeJsWorld, timeout=500):
        '''
        @param: scriptSource QString
        @return: QVariant
        '''
        loop = QEventLoop()  # QPointer<QEventLoop>
        result = None
        QTimer.singleShot(timeout, loop.quit)

        def runCb(res):
            nonlocal result
            if loop and loop.isRunning():
                result = res
                loop.quit()

        self.runJavaScript(scriptSource, worldId, runCb)
        loop.exec_(QEventLoop.ExcludeUserInputEvents)

        return result

    def mapToViewport(self, pos):
        '''
        @param: pos QPointF
        @return: QPointF
        '''
        return QPointF(pos.x() / self.zoomFactor(), pos.y() / self.zoomFactor())

    def hitTestContent(self, pos):
        '''
        @param: QPoint
        @return: WebHitTestResult
        '''
        return WebHitTestResult(self, pos)

    def scroll(self, x, y):
        pass

    def setScrollPosition(self, pos):
        '''
        @param: pos QPointF
        '''
        pass

    # override
    def javaScriptPrompt(self, securityOrigin, msg, defaultValue):
        '''
        @param: securityOrigin QUrl
        @param: msg QString
        @param: defaultValue QString
        @return: ret bool, result QString
        '''
        pass

    # override
    def javaScriptConfirm(self, securityOrigin, msg):
        '''
        @param: securityOrigin QUrl
        @param: msg QString
        '''
        pass

    # override
    def javaScriptAlert(self, securityOrigin, msg):
        '''
        @param: securityOrigin QUrl
        @param: msg QString
        '''
        pass

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        '''
        @param: level JavaScriptConsoleMessagelevel
        @param: message QString
        @param: lineNumber int
        @param: sourceID QString
        '''
        pass

    def autoFillUsernames(self):
        return []  # QStringList

    def registerProtocolHandlerRequestUrl(self):
        '''
        @return: QUrl
        '''
        return QUrl()

    def registerProtocolHandlerRequestScheme(self):
        '''
        @return: QString
        '''
        return ''

    def isRunningLoop(self):
        return self._runningLoop

    def isLoading(self):
        return self._loadProgress < 100

    @classmethod
    def internalSchemes(cls):
        '''
        @return: QStringList
        '''
        return [
            'http', 'https', 'file', 'ftp', 'data', 'about', 'view-source', 'chrome'
        ]

    @classmethod
    def supportedSchemes(cls):
        '''
        @return: QStringList
        '''
        if cls._s_supportedSchemes:
            cls._s_supportedSchemes = cls.internalSchemes()
        return cls._s_supportedSchemes

    @classmethod
    def addSupportedScheme(cls, scheme):
        cls._s_supportedSchemes = cls.supportedSchemes()[:]
        if scheme not in cls._s_supportedSchemes:
            cls._s_supportedSchemes.append(scheme)

    @classmethod
    def removeSupportedScheme(cls, scheme):
        cls._s_supportedSchemes.remove(scheme)

    # Q_SIGNALS
    privacyChanged = pyqtSignal(bool)  # status
    printRequested = pyqtSignal()
    # url, NavigationType type_, isMainFrame
    navigationRequestAccepted = pyqtSignal(QUrl, int, bool)

    # protected Q_SLOTS:
    def _progress(self, prog):
        '''
        @param: prog int
        '''
        self._loadProgress = prog

        secStatus = self.url().scheme() == 'https'

        if secStatus != self._secureStatus:
            self._secureStatus = secStatus
            self.privacyChanged.emit(secStatus)

    def _finished(self):
        self._progress(100)

        # File scheme watcher
        if self.url().scheme() == 'file':
            info = QFileInfo(self.url().toLocalFile())
            if info.isFile():
                if not self._fileWatcher:
                    self._fileWatcher = DelayedFileWatcher(self)
                    self._fileWatcher.delayedFileChanged.connect(self._watchedFileChanged)

                filePath = self.url().toLocalFile()

                if QFile.exists(filePath) and filePath not in self._fileWatcher.files():
                    self._fileWatcher.addPath(filePath)
        elif self._fileWatcher and self._fileWatcher.files():
            self._fileWatcher.removePathes(self._fileWatcher.files())

        # AutoFill
        self._autoFillUsernames = gVar.app.autoFill().completePage(self, self.url())

    # private Q_SLOTS:
    def _urlChanged(self, url):
        '''
        @param: url QUrl
        '''
        if self.isLoading():
            self._blockAlerts = False

    def _watchedFileChanged(self, file_):
        '''
        @param: file_ QString
        '''
        if self.url().toLocalFile() == file_:
            self.triggerAction(QWebEnginePage.Reload)

    def _windowCloseRequested(self):
        view = self.view()
        if not view:
            return
        view.closeView()

    def _fullScreenRequested(self, fullScreenRequest):
        '''
        @param: fullScreenRequest QWebEngineFullScreenRequest
        '''
        pass

    def _featurePermissionRequested(self, origin, feature):
        '''
        @param: origin QUrl
        @param: feature QWebEnginePage::feature
        '''
        pass

    def _renderProcessTerminated(self, terminationStatus, exitCode):
        '''
        @param: terminationStatus RenderProcessTerminationStatus
        @param: exitCode int
        '''
        pass

    # private:
    # override
    def acceptNavigationRequest(self, url, type_, isMainFrame):
        '''
        @param: url QUrl
        @param: type_ QWebEnginePage.NavigationType
        @param: isMainFrame bool
        '''
        if gVar.app.isClosing():
            return super().acceptNavigationRequest(url, type_, isMainFrame)

        # TODO: plugins
        #if not gVar.app.plugins().acceptNavigationRequest(self, url, type_, isMainFrame):
        #    return False

        if url.scheme() == 'app':
            if url.path() == 'AddSearchProvider':
                query = QUrlQuery(url)
                gVar.app.searchEnginesManager().addEngine(query.queryItemValue('url'))
                return False
            # if QTWEBENGINEWIDGETS_VERSION < QT_VERSION_CHECK(5, 12, 0)
            # elif url.path() == 'PrintPage':
            #   self.printRequested.emit()
            #   return False

        result = super().acceptNavigationRequest(url, type_, isMainFrame)
        if result:
            # TODO:
            #if isMainFrame:
            #    isWeb = url.scheme() in ('http', 'https', 'file')
            #    globalJsEnabled = gVar.app.webSettings().testAttribute(QWebEngineSettings.JavascriptEnabled)
            #    self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, isWeb and globalJsEnabled or True)

            self.navigationRequestAccepted.emit(url, type_, isMainFrame)
        return result

    # override
    def certificateError(self, error):
        '''
        @param: error QWebEngineCertificateError
        '''
        pass

    # override
    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):
        '''
        @param: mode FileSelectionMode
        @param: oldFiles QStringList
        @param: acceptedMimeTypes QStringList
        @return: QStringList
        '''
        pass

    # override
    def createWindow(self, type_):
        '''
        @param: type_ QWebEnginePage::WebWindowType
        @return: QWebEnginePage
        '''
        # TabbedWebView
        tView = self.view()
        if tView:
            window = tView.browserWindow()
        else:
            window = gVar.app.getWindow()

        def createTab(pos):
            index = window.tabWidget().addViewByUrl(QUrl(), pos)
            view = window.weViewByIndex(index)
            view.setPage(WebPage())
            if tView:
                tView.webTab().addChildTab(view.webTab())
            # Workaround focus issue when creating tab
            if pos & const.NT_SelectedTab:
                view.setFocus()

                def x():
                    if view and view.webTab().isCurrentTab():
                        view.setFocus()
                QTimer.singleShot(100, x)
            return view.page()

        if type_ == QWebEnginePage.WebBrowserWindow:
            window = gVar.app.createWindow(const.BW_NewWindow)
            page = WebPage()
            window.setStartPage(page)
            return page

        if type_ == QWebEnginePage.WebDialog:
            if not gVar.appSettings.openPopupsInTabs:
                from mc.popupwindow.PopupWebView import PopupWebView
                from mc.popupwindow.PopupWindow import PopupWindow
                view = PopupWebView()
                view.setPage(WebPage())
                popup = PopupWindow(view)
                popup.show()
                window.addDeleteOnCloseWidget(popup)
                return view.page()
            # else fallthrough

        if type_ == QWebEnginePage.WebBrowserTab:
            return createTab(const.NT_CleanSelectedTab)

        if type_ == QWebEnginePage.WebBrowserBackgroundTab:
            return createTab(const.NT_CleanNotSelectedTab)

        return None

    def handleUnknownProtocol(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def desktopServicesOpen(self, url):
        '''
        @param: url QUrl
        '''
        pass
