from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineScript
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from PyQt5.Qt import QTime
from PyQt5.Qt import QPointF
from PyQt5.Qt import QWebChannel
from mc.common.globalvars import gVar
from PyQt5.Qt import QUrlQuery
from PyQt5.Qt import QDir
from mc.common import const
from PyQt5.Qt import QTimer

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

        # TODO:
        #channel = QWebChannel(self)
        self.windowCloseRequested.connect(self._windowCloseRequested)

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
        pass

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
        pass

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
        pass

    def _finished(self):
        pass

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

    def _reanderProcessTerminated(self, terminationStatus, exitCode):
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
