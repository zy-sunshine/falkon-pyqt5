from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineScript
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineRegisterProtocolHandlerRequest
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from PyQt5.Qt import QTime
from PyQt5.Qt import QPointF
from PyQt5.Qt import QWebChannel
from PyQt5.Qt import QEventLoop
from PyQt5.Qt import QUrlQuery
from PyQt5.Qt import QDir
from PyQt5.Qt import QTimer
from PyQt5.Qt import QFileInfo, QFile
from PyQt5.Qt import Qt
from PyQt5.Qt import QStyle
from PyQt5.Qt import QDesktopServices
from PyQt5.QtCore import qEnvironmentVariable
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QFrame
from mc.common.globalvars import gVar
from mc.common import const
from mc.tools.Scripts import Scripts
from mc.tools.DelayedFileWatcher import DelayedFileWatcher
from mc.other.CheckBoxDialog import CheckBoxDialog
from mc.tools.IconProvider import IconProvider
from .javascript.ExternalJsObject import ExternalJsObject
from .WebHitTestResult import WebHitTestResult

class CloseableFrame(QFrame):
    closeRequested = pyqtSignal()
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        if event.key() == Qt.Key_Escape:
            self.closeRequested.emit()
        super().keyPressEvent(event)

class WebPage(QWebEnginePage):
    _s_kEnableJsOutput = qEnvironmentVariable('APP_ENABLE_JS_OUTPUT') != ''
    _s_kEnableJsNonBlockDialogs = qEnvironmentVariable('APP_ENABLE_JS_NONBLOCK_DIALOGS', 'yes') != '0'
    # JsWorld
    UnsafeJsWorld = QWebEngineScript.MainWorld
    SafeJsWorld = QWebEngineScript.ApplicationWorld

    # static members
    s_lastUploadLocation = ''
    s_lastUnsupportedUrl = QUrl()
    s_lastUnsupportedUrlTime = QTime()

    # private members
    _s_lastUploadLocation = QDir.homePath()
    _s_supportedSchemes = []  # QStringList
    def __init__(self, parent=None):
        super().__init__(gVar.app.webProfile(), parent)
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

        if const.QTWEBENGINEWIDGETS_VERSION >= const.QT_VERSION_CHECK(5, 11, 0):
            def registerProtocolHandlerFunc(request):
                '''
                @param: request QWebEngineRegisterProtocolHandlerRequest
                '''
                del self._registerProtocolHandlerRequest
                self._registerProtocolHandlerRequest = QWebEngineRegisterProtocolHandlerRequest(request)
            self.registerProtocolHandlerRequested.connect(registerProtocolHandlerFunc)

        if const.QTWEBENGINEWIDGETS_VERSION >= const.QT_VERSION_CHECK(5, 12, 0):
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
        # return static_cast<WebView*>(QWebEnginePage::view())
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
        self.runJavaScript("window.scrollTo(window.scrollX + %s, window.scrollY + %s)" %
                (x, y), self.SafeJsWorld)

    def setScrollPosition(self, pos):
        '''
        @param: pos QPointF
        '''
        # QPointF
        v = self.mapToViewport(pos.toPoint())
        self.runJavaScript("window.scrollTo(%s, %s)" % (v.x(), v.y()), self.SafeJsWorld)

    # override
    def javaScriptPrompt(self, securityOrigin, msg, defaultValue):
        '''
        @param: securityOrigin QUrl
        @param: msg QString
        @param: defaultValue QString
        @return: ret bool, result QString
        '''
        if not self._s_kEnableJsNonBlockDialogs:
            return super().javaScriptPrompt(securityOrigin, msg, defaultValue)

        if self._runningLoop:
            return False, defaultValue

        widget = CloseableFrame(self.view().overlayWidget())

        widget.setObjectName('jsFrame')
        ui = uic.loadUi('mc/webengine/JsPrompt.ui', widget)
        ui.message.setText(msg)
        ui.lineEdit.setText(defaultValue)
        ui.lineEdit.setFocus()
        widget.resize(self.view().size())
        widget.show()

        # QAbstractButton
        clicked = None

        def clickedCb(button):
            nonlocal clicked
            clicked = button

        ui.buttonBox.clicked.connect(clickedCb)
        ui.lineEdit.returnPressed.connect(ui.buttonBox.button(QDialogButtonBox.Ok).animateClick)
        self.view().viewportResized.connect(widget.resize)

        eLoop = QEventLoop()
        self._runningLoop = eLoop
        widget.closeRequested.connect(eLoop.quit)
        ui.buttonBox.clicked.connect(eLoop.quit)

        if eLoop.exec_() == 1:
            return False
        self._runningLoop = None

        result = ui.lineEdit.text()
        ret = ui.buttonBox.buttonRole(clicked) == QDialogButtonBox.AcceptRole

        self.view().setFocus()
        self.view().viewportResized.disconnect(widget.resize)
        ui.buttonBox.clicked.disconnect(clickedCb)

        widget.close()
        widget.deleteLater()

        return ret, result

    # override
    def javaScriptConfirm(self, securityOrigin, msg):
        '''
        @param: securityOrigin QUrl
        @param: msg QString
        '''
        if not self._s_kEnableJsNonBlockDialogs:
            return super().javaScriptConfirm(securityOrigin, msg)

        if self._runningLoop:
            return False

        widget = CloseableFrame(self.view().overlayWidget())

        widget.setObjectName('jsFrame')
        ui = uic.loadUi('mc/webengine/JsConfirm.ui', widget)
        ui.message.setText(msg)
        ui.buttonBox.button(QDialogButtonBox.Ok).setFocus()
        widget.resize(self.view().size())
        widget.show()

        # QAbstractButton
        clicked = None

        def clickedCb(button):
            nonlocal clicked
            clicked = button

        ui.buttonBox.clicked.connect(clickedCb)
        self.view().viewportResized.connect(widget.resize)

        eLoop = QEventLoop()
        self._runningLoop = eLoop
        widget.closeRequested.connect(eLoop.quit)
        ui.buttonBox.clicked.connect(eLoop.quit)

        if eLoop.exec_() == 1:
            return False
        self._runningLoop = None

        result = ui.buttonBox.buttonRole(clicked) == QDialogButtonBox.AcceptRole

        self.view().setFocus()
        self.view().viewportResized.disconnect(widget.resize)
        ui.buttonBox.clicked.disconnect(clickedCb)

        widget.close()
        widget.deleteLater()

        return result

    # override
    def javaScriptAlert(self, securityOrigin, msg):
        '''
        @param: securityOrigin QUrl
        @param: msg QString
        '''
        if self._blockAlerts or self._runningLoop:
            return

        if not self._s_kEnableJsNonBlockDialogs:
            title = _('JavaScript alert')
            if self.url().host():
                title = '%s - %s' % (title, self.url().host())

            dialog = CheckBoxDialog(QMessageBox.Ok, self.view())
            dialog.setDefaultButton(QMessageBox.Ok)
            dialog.setWindowTitle(title)
            dialog.setText(msg)
            dialog.setCheckBoxText(_('Prevent this page from creating additional dialogs'))
            dialog.setIcon(QMessageBox.Information)
            dialog.exec_()

            self._blockAlerts = dialog.isChecked()
            return

        widget = CloseableFrame(self.view().overlayWidget())

        widget.setObjectName('jsFrame')
        ui = uic.loadUi('mc/webengine/JsAlert.ui', widget)
        ui.message.setText(msg)
        ui.buttonBox.button(QDialogButtonBox.Ok).setFocus()
        widget.resize(self.view().size())
        widget.show()

        self.view().viewportResized.connect(widget.resize)

        eLoop = QEventLoop()
        self._runningLoop = eLoop
        widget.closeRequested.connect(eLoop.quit)
        ui.buttonBox.clicked.connect(eLoop.quit)

        if eLoop.exec_() == 1:
            return
        self._runningLoop = None

        self._blockAlerts = ui.preventAlerts.isChecked()

        self.view().setFocus()
        self.view().viewportResized.disconnect(widget.resize)

        widget.close()
        widget.deleteLater()

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        '''
        @param: level JavaScriptConsoleMessagelevel
        @param: message QString
        @param: lineNumber int
        @param: sourceID QString
        '''
        if not self._s_kEnableJsOutput:
            return

        prefix = ''
        if level == self.InfoMessageLevel:
            prefix = '[I]'
        elif level == self.WarningMessageLevel:
            prefix = '[W]'
        elif level == self.ErrorMessageLevel:
            prefix = '[E]'

        msg = '%s%s:%s %s' % (prefix, sourceID, lineNumber, message)
        print(msg)

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
        self.view().requestFullScreen(fullScreenRequest.toggleOn())

        accepted = fullScreenRequest.toggleOn() == self.view().isFullScreen()

        if accepted:
            fullScreenRequest.accept()
        else:
            fullScreenRequest.reject()

    def _featurePermissionRequested(self, origin, feature):
        '''
        @param: origin QUrl
        @param: feature QWebEnginePage::feature
        '''
        if feature == self.MouseLock and self.view().isFullScreen():
            self.setFeaturePermission(origin, feature, self.PermissionGrantedByUser)
        else:
            gVar.app.html5PermissionsManager().requestPermissions(self, origin, feature)

    def _renderProcessTerminated(self, terminationStatus, exitCode):
        '''
        @param: terminationStatus RenderProcessTerminationStatus
        @param: exitCode int
        '''
        if terminationStatus == self.NormalTerminationStatus:
            return

        def showCrashHtmlCb():
            page = gVar.appTools.readAllFileContents(':html/tabcrash.html')
            img = gVar.appTools.pixmapToDataUrl(IconProvider.standardIcon(
                QStyle.SP_MessageBoxWarning).pixmap(45)).toString()
            page = page.replace("%IMAGE%", img) \
                .replace("%TITLE%", _("Failed loading page")) \
                .replace("%HEADING%", _("Failed loading page")) \
                .replace("%LI-1%", _("Something went wrong while loading this page.")) \
                .replace("%LI-2%", _("Try reloading the page or closing some tabs to make more memory available.")) \
                .replace("%RELOAD-PAGE%", _("Reload page"))
            page = gVar.appTool.applyDirectionToPage(page)
            self.setHtml(page, self.url())

        QTimer.singleShot(0, showCrashHtmlCb)

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
            if const.QTWEBENGINEWIDGETS_VERSION < const.QT_VERSION_CHECK(5, 12, 0):
                if url.path() == 'PrintPage':
                    self.printRequested.emit()
                    return False

        result = super().acceptNavigationRequest(url, type_, isMainFrame)
        if result:
            if isMainFrame:
                isWeb = url.scheme() in ('http', 'https', 'file')
                globalJsEnabled = gVar.app.webSettings().testAttribute(QWebEngineSettings.JavascriptEnabled)
                if isWeb:
                    enable = globalJsEnabled
                else:
                    enable = True
                self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, enable)

            self.navigationRequestAccepted.emit(url, type_, isMainFrame)
        return result

    # override
    def certificateError(self, error):
        '''
        @param: error QWebEngineCertificateError
        '''
        return gVar.app.networkManager().certificateError(error, self.view())

    # override
    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):
        '''
        @param: mode FileSelectionMode
        @param: oldFiles QStringList
        @param: acceptedMimeTypes QStringList
        @return: QStringList
        '''
        files = []  # QStringList
        suggestedFileName = self._s_lastUploadLocation
        if oldFiles and oldFiles[0]:
            suggestedFileName = oldFiles[0]

        if mode == self.FileSelectOpen:
            path = gVar.appTools.getOpenFileName('WebPage-ChooseFile', self.view(),
                _('Choose file...'), suggestedFileName)
            files = [path, ]
        elif mode == self.FileSelectOpenMultiple:
            files = gVar.appTools.getOpenFileNames('WebPage-ChooseFile', self.view(),
                _('Choose file...'), suggestedFileName)
        else:
            files = super().chooseFiles(mode, oldFiles, acceptedMimeTypes)
        if files:
            self._s_lastUploadLocation = files[0]

        return files

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
            view = window.weView(index)
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
        protocol = url.scheme()

        if protocol == 'mailto':
            self.desktopServicesOpen(url)
            return

        if protocol in gVar.appSettings.blockedProtocols:
            print('DEBUG: WebPage::handleUnknownProtocol', protocol, 'is blocked!')
            return

        if protocol in gVar.appSettings.autoOpenProtocols:
            self.desktopServicesOpen(url)
            return

        dialog = CheckBoxDialog(QMessageBox.Yes | QMessageBox.No, self.view())
        dialog.setDefaultButton(QMessageBox.Yes)

        wrappedUrl = gVar.appTools.alignTextToWidth(url.toString(), '<br/>',
                dialog.fontMetrics(), 450)
        text = _("Falkon cannot handle <b>%s:</b> links. The requested link "
                "is <ul><li>%s</li></ul>Do you want Falkon to try "
                "open this link in system application?") % (protocol, wrappedUrl)

        dialog.setText(text)
        dialog.setCheckBoxText(_("Remember my choice for this protocol"))
        dialog.setWindowTitle(_("External Protocol Request"))
        dialog.setIcon(QMessageBox.Question)
        ret = dialog.exec_()
        if ret == QMessageBox.Yes:
            if dialog.isChecked():
                gVar.appSettings.autoOpenProtocols.append(protocol)
                gVar.appSettings.saveSettings()

            QDesktopServices.openUrl(url)
        elif ret == QMessageBox.No:
            if dialog.isChecked():
                gVar.appSettings.autoOpenProtocols.append(protocol)
                gVar.appSettings.saveSettings()

    def desktopServicesOpen(self, url):
        '''
        @param: url QUrl
        '''
        # Open same url only once in 2 secs
        sameUrlTimeout = 2 * 1000
        if self.s_lastUnsupportedUrl != url or self.s_lastUnsupportedUrlTime.isNull() or \
                self.s_lastUnsupportedUrlTime.elapsed() > sameUrlTimeout:
            self.s_lastUnsupportedUrl = url
            self.s_lastUnsupportedUrlTime.restart()
            QDesktopServices.openUrl(url)
        else:
            print('WARNING: WebPage::desktopServicesOpen Url', url, 'has already been opened!\n',
                'Ignoring it to prevent infinite loop!')
