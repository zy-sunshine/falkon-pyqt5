from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QSize
from PyQt5.Qt import QWidget
from PyQt5.Qt import QUrl
from PyQt5.Qt import QPointF
from PyQt5.Qt import QRect
from PyQt5.Qt import QEvent
from PyQt5.Qt import QTimer
from PyQt5.Qt import QPalette
from PyQt5.Qt import QMouseEvent
from PyQt5.Qt import QWheelEvent
from PyQt5.Qt import QKeyEvent
from PyQt5.Qt import QStyle
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QPrinter
from PyQt5.Qt import QPrintDialog
from PyQt5.Qt import QAbstractPrintDialog
from PyQt5.Qt import QDialog
from PyQt5.Qt import QDesktopServices
from PyQt5.Qt import qFuzzyCompare
from PyQt5.Qt import QAction

from .WebPage import WebPage
from mc.tools.WheelHelper import WheelHelper
from mc.common.globalvars import gVar
from .WebInspector import WebInspector
from .WebScrollBarManager import WebScrollBarManager
from mc.tools.IconProvider import IconProvider
from mc.common import const
from mc.other.SiteInfo import SiteInfo

class WebView(QWebEngineView):
    s_forceContextMenuOnMouseRelease = False

    def __init__(self, parent=None):
        super(WebView, self).__init__(parent)
        self._currentZoomLevel = 0
        self._progress = 0
        self._backgroundActivity = False

        self._clickedUrl = QUrl()
        self._clickedPos = QPointF()

        self._page = None  # WebPage
        self._firstLoad = False  # False

        self._rwhvqt = None  # QPointer<QWidget>
        self._wheelHelper = WheelHelper()

        self.loadStarted.connect(self._slotLoadStarted)
        self.loadProgress.connect(self._slotLoadProgress)
        self.loadFinished.connect(lambda ok: WebView._slotLoadFinished(self, ok))
        self.iconChanged.connect(self._slotIconChanged)
        self.urlChanged.connect(self._slotUrlChanged)
        self.titleChanged.connect(self._slotTitleChanged)

        self._currentZoomLevel = self.zoomLevels().index(100)

        self.setAcceptDrops(True)
        self.installEventFilter(self)
        if self.parentWidget():
            self.parentWidget().installEventFilter(self)

        WebInspector.registerView(self)

    def __del__(self):
        gVar.app.plugins().emitWebPageDeleted(self._page)

        WebInspector.unregisterView(self)
        WebScrollBarManager.instance().removeWebView(self)

    def icon(self, allowNull=False):
        '''
        @return: QIcon
        '''
        icon = super().icon()
        if not icon.isNull():
            return icon

        scheme = self.url().scheme()
        if scheme == 'ftp':
            return IconProvider.standardIcon(QStyle.SP_ComputerIcon)

        if scheme == 'file':
            return IconProvider.standardIcon(QStyle.SP_DriveHDIcon)

        return IconProvider.iconForUrl(self.url(), allowNull)

    def title(self, allowEmpty=False):
        '''
        @return: QString
        '''
        title = super().title()

        if allowEmpty:
            return title

        if self.url().isEmpty():
            u = self._page.requestedUrl()
        else:
            u = self.url()

        if not title:
            title = u.host()

        if not title:
            title = u.toString(QUrl.RemoveFragment)

        if not title or title == 'about:blank':
            return 'Empty Page'

        return title

    def page(self):
        '''
        @return: WebPage
        '''
        return self._page

    def setPage(self, page):
        '''
        @param: page WebPage
        '''
        if page == self._page:
            return

        if self._page:
            if self._page.isLoading():
                self._page.loadProgress.emit(100)
                self._page.loadFinished.emit(True)
            # gVar.app.plugins().emitWebPageDeleted(self._page)
            self._page.setView(None)

        page.setParent(self)
        QWebEngineView.setPage(self, page)
        del self._page
        self._page = page

        if self._page.isLoading():
            self.loadStarted.emit()
            self.loadProgress.emit(self._page._loadProgress)

        self._page.privacyChanged.connect(self.privacyChanged)
        self._page.printRequested.connect(self.printPage)

        # Set default zoom level
        self.zoomReset()

        # actions needs to be initialized for every QWebEngine change
        self._initializeActions()

        # Scrollbars must be added only after QWebEnginePage is set
        gVar.webScrollBarManager.addWebView(self)

        self.pageChanged.emit(self._page)
        # gVar.app.plugins().emitWebPageCreated(self._page)

    def loadByUrl(self, url):
        '''
        @param: url QUrl
        '''
        if self._page and not self._page.acceptNavigationRequest(url,
                QWebEnginePage.NavigationTypeTyped, True):
            return

        super().load(url)

        if not self._firstLoad:
            self._firstLoad = True
            WebInspector.pushView(self)

    def loadByReq(self, request):
        '''
        @param: request LoadRequest
        '''
        reqUrl = request.url()

        if reqUrl.isEmpty():
            return

        if reqUrl.scheme() == 'javascript':
            scriptSource = reqUrl.toString()[11:]
            # Is the javascript source percent encoded or not?
            # Looking for % character in source should work in most cases
            if '%' in scriptSource:
                self.page().runJavaScript(
                    QUrl.fromPercentEncoding(scriptSource)
                )
            else:
                self.page().runJavaScript(scriptSource)
            return

        if self.isUrlValid(reqUrl):
            self._loadRequest(request)

    def isLoading(self):
        return self._progress < 100

    def loadingProgress(self):
        '''
        @return: int
        '''
        return self._progress

    def backgroundActivity(self):
        '''
        @return: bool
        '''
        return self._backgroundActivity

    # Set zoom level (0 - 17)
    def zoomLevel(self):
        return self._currentZoomLevel

    def setZoomLevel(self, level):
        self._currentZoomLevel = level
        self._applyZoom()

    def mapToViewport(self, pos):
        '''
        @param: pos QPointF
        @return: QPointF
        '''
        return self.page().mapToViewport(pos)

    def scrollBarGeometry(self, orientation):
        '''
        @param: orientation Qt::Orientation
        @return: QRect
        '''
        # QScrollBar s
        # TODO: const_cast<WebView*>(self)
        s = WebScrollBarManager.instance().scrollBar(orientation, self)
        if s and s.isVisible():
            return s.geometry()
        else:
            return QRect()

    def addNotification(self, notif):
        '''
        @param: notif QWidget
        '''
        self.showNotification.emit(notif)

    # override
    def eventFilter(self, obj, event):  # noqa C901
        '''
        @param: obj QObject
        @param: event QEvent
        '''
        # TODO:
        return super().eventFilter(obj, event)

        evtype = event.type()
        # Keyboard events are sent to parent widget
        if obj == self and evtype == QEvent.ParentChange and self.parentWidget():
            self.parentWidget().installEventFilter(self)

        # Hack to find widget that receives input events
        if obj == self and evtype == QEvent.ChildAdded:
            # if QTWEBENGINEWIDGETS_VERSION >= QT_VERSION_CHECK(5, 12, 0)
            # TODO: qobject_cast<QWidget*>(static_cast<QChildEvent*>(event)->child());
            child = event.child()

            def xxx():
                if child and child.inherits('QWebEngineCore::RenderWidgetHostViewQtDelegateWidget'):
                    self._rwhvqt = child
                    self._rwhvqt.installEvent(self)
                    # TODO: QQuickWidget *w =
                    # qobject_cast<QQuickWidget*>(m_rwhvqt)
                    w = self._rwhvqt
                    if w:
                        w.setClearColor(self.palette().color(QPalette.Window))
            QTimer.singleShot(0, xxx)

            # else // QTWEBENGINEWIDGETS_VERSION >= QT_VERSION_CHECK(5, 12, 0)
            if 0:
                def yyy():  # TODO: yyy(self?)
                    focusProxy = self.focusProxy()
                    if focusProxy and self._rwhvqt != focusProxy:
                        self._rwhvqt = focusProxy
                        self._rwhvqt.installEventFilter(self)
                        # qobject_cast<QQuickWidget*>(m_rwhvqt)
                        w = self._rwhvqt
                        if w:
                            w.setClearColor(self.palette().color(QPalette.Window))
                QTimer.singleShot(0, yyy)

        def __handleEvent(f, t):
            wasAccepted = event.isAccepted()
            event.setAccepted(False)
            f(event)
            ret = event.isAccepted()
            event.setAccepted(wasAccepted)
            return ret
        # Forward events to WebView
        if obj == self._rwhvqt:
            if evtype == QEvent.MouseButtonPress:
                __handleEvent(self._mousePressEvent, QMouseEvent)
            elif evtype == QEvent.MouseButtonRelease:
                __handleEvent(self.mouseReleaseEvent, QMouseEvent)
            elif evtype == QEvent.MouseMove:
                __handleEvent(self.mouseMoveEvent, QMouseEvent)
            elif evtype == QEvent.Wheel:
                __handleEvent(self._wheelEvent, QWheelEvent)

        if obj == self.parentWidget():
            if evtype == QEvent.KeyPress:
                __handleEvent(self._keyPressEvent, QKeyEvent)
            if evtype == QEvent.KeyRelease:
                __handleEvent(self._keyReleaseEvent, QKeyEvent)

        # Block already handled events
        if obj == self:
            if evtype in (QEvent.KeyPress, QEvent.KeyRelease,
                    QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                    QEvent.MouseMove, QEvent.Wheel):
                return True
            if evtype == QEvent.Hide:
                if self.isFullScreen():
                    self.triggerPageAction(QWebEnginePage.ExitFullScreen)

        res = super().eventFilter(obj, event)

        if obj == self._rwhvqt:
            if evtype in (QEvent.FocusIn, QEvent.FocusOut):
                self.focusChanged.emit(self.hasFocus())

        return res

    def inputWidget(self):
        '''
        @return: QWidget
        '''
        import ipdb; ipdb.set_trace()
        if self._rwhvqt:
            return self._rwhvqt
        else:
            # const_cast<WebView*>(this)
            return self

    # pure virtual method
    def overlayWidget(self):
        raise NotImplementedError

    @classmethod
    def isUrlValid(cls, url):
        '''
        @brief: Valid url must have scheme and actrually contains something (therefore scheme:// is invalid)
        @param: url QUrl
        @return: bool
        '''
        if url.isValid() and url.scheme() and (url.host() or url.path() or url.hasQuery()):
            return True
        else:
            return False

    @classmethod
    def zoomLevels(cls):
        '''
        @param: QList<int>
        '''
        return [ 30, 40, 50, 67, 80, 90, 100, 110, 120, 133, 150, 170, 200,
                220, 233, 250, 270, 285, 300 ]

    # Force context menu event to be sent on mouse release
    # This allows to override right mouse button events (eg. for mouse gestures)
    @classmethod
    def forceContextMenuOnMouseRelease(cls):
        return cls.s_forceContextMenuOnMouseRelease

    @classmethod
    def setForceContextmenuOnMouseRelease(cls, force):
        cls.s_forceContextMenuOnMouseRelease = force

    # Q_SIGNALS:
    pageChanged = pyqtSignal(WebPage) # page
    focusChanged = pyqtSignal(bool)
    viewportResized = pyqtSignal(QSize)
    showNotification = pyqtSignal(QWidget)
    privacyChanged = pyqtSignal(bool)
    zoomLevelChanged = pyqtSignal(int)
    backgroundActivityChanged = pyqtSignal(bool)

    # public Q_SLOTS:
    def zoomIn(self):
        if self._currentZoomLevel < len(self.zoomLevels()) - 1:
            self._currentZoomLevel += 1
            self._applyZoom()

    def zoomOut(self):
        if self._currentZoomLevel > 0:
            self._currentZoomLevel -= 1
            self._applyZoom()

    def zoomReset(self):
        if self._currentZoomLevel != gVar.appSettings.defaultZoomLevel:
            self._currentZoomLevel = gVar.appSettings.defaultZoomLevel
            self._applyZoom()

    def editUndo(self):
        self.triggerPageAction(QWebEnginePage.Undo)

    def editRedo(self):
        self.triggerPageAction(QWebEnginePage.Redo)

    def editCut(self):
        self.triggerPageAction(QWebEnginePage.Cut)

    def editCopy(self):
        self.triggerPageAction(QWebEnginePage.Copy)

    def editPaste(self):
        self.triggerPageAction(QWebEnginePage.Paste)

    def editSelectAll(self):
        self.triggerPageAction(QWebEnginePage.SelectAll)

    def editDelete(self):
        ev = QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
        QApplication.sendEvent(self, ev)

    def reloadBypassCache(self):
        self.triggerPageAction(QWebEnginePage.ReloadAndBypassCache)

    def back(self):
        # QWebEngineHistory
        history = self.page().history()

        if history.canGoBack():
            history.back()

            self.urlChanged.emit(self.url())

    def forward(self):
        history = self.page().history()

        if history.canGoForward():
            history.forward()

            self.urlChanged.emit(self.url())

    def printPage(self):
        assert(self._page)

        printer = QPrinter()
        printer.setCreator('APP %s (%s)' % (const.VERSION, const.WWWADDRESS))
        printer.setDocName(gVar.appTools.filterCharsFromFilename(self.title()))
        dialog = QPrintDialog(printer, self)
        dialog.setOptions(QAbstractPrintDialog.PrintToFile | QAbstractPrintDialog.PrintShowPageSize)
        if not const.OS_WIN:
            dialog.setOption(QAbstractPrintDialog.PrintPageRange)
            dialog.setOption(QAbstractPrintDialog.PrintCollateCopies)

        if dialog.exec_() == QDialog.Accepted:
            if dialog.printer().outputFormat() == QPrinter.PdfFormat:
                self._page.printToPdf(dialog.printer().outputFileName(),
                        dialog.printer().pageLayout())
                del dialog
            else:
                self._page.print_(dialog.printer())

    def showSource(self):
        # view-source: doesn't work on itself and custom schemes
        scheme = self.url().scheme()
        if scheme == 'view-source' or scheme == 'app' or scheme == 'qrc':
            def htmlFunc(html):
                print(html)
            self.page().toHtml(htmlFunc)

    def sendPageByEmail(self):
        body = QUrl.toPercentEncoding(self.url().toEncoded())
        subject = QUrl.toPercentEncoding(self.title())
        mailUrl = QUrl.fromEncoded('mailto:%20?body=%s&subject=%s' % (body, subject))
        QDesktopServices.openUrl(mailUrl)

    def openUrlInNewTab(self, url, position):
        '''
        @param: url QUrl
        @param: position Qz::NewTabPositionFlags
        '''
        self.loadInNewTab(url, position)

    # pure virtual method
    def closeView(self):
        raise NotImplementedError

    # pure virtual method
    def loadInNewTab(self, req, position):
        '''
        @param: req LoadRequest
        @param: position Qz::NewTabPositionFlags
        '''
        raise NotImplementedError

    # pure virtual method
    def isFullScreen(self):
        raise NotImplementedError

    # pure virtual method
    def requestFullScreen(self, enable):
        raise NotImplementedError

    # protected Q_SLOTS:
    def _slotLoadStarted(self):
        self._progress = 0
        if not self.title(True):
            self.titleChanged.emit(self.title())

    def _slotLoadProgress(self, progress):
        if self._progress < 100:
            self._progress = progress

        # QtWebEngine sometimes forgets applied zoom factor
        if qFuzzyCompare(self.zoomFactor(), self.zoomLevels()[self._currentZoomLevel] / 100.0):
            self._applyZoom()

    def _slotLoadFinished(self, ok):
        '''
        @param: ok bool
        '''
        self._progress = 100

        if ok:
            gVar.app.history().addHistoryEntryByView(self)

    def _slotIconChanged(self):
        IconProvider.instance().saveIcon(self)

    def _slotUrlChanged(self, url):
        '''
        @param: url QUrl
        '''
        if not url.isEmpty() and not self.title(True):
            # Don't treat this as background activity change
            oldActivity = self._backgroundActivity
            self._backgroundActivity = True
            self.titleChanged.emit(self.title())
            self._backgroundActivity = oldActivity

    def _slotTitleChanged(self, title):
        '''
        @param: title QString
        '''
        if not self.isVisible() and not self.isLoading() and not self._backgroundActivity:
            self._backgroundActivity = True
            self.backgroundActivityChanged.emit(self._backgroundActivity)

    # Context menu slots
    def _openUrlInNewWindow(self):
        action = self.sender()
        if isinstance(action, QAction):
            gVar.app.createWindow(const.BW_NewWindow, action.data().toUrl())

    def _sendTextByMail(self):
        action = self.sender()
        if isinstance(action, QAction):
            body = QUrl.toPercentEncoding(action.data().toString())
            mailUrl = QUrl.fromEncoded('mailto:%20?body=%s' % body)
            QDesktopServices.openUrl(mailUrl)

    def _copyLinkToClipboard(self):
        action = self.sender()
        if isinstance(action, QAction):
            QApplication.clipboard().setText(action.data().toUrl().toEncoded())

    def _savePageAs(self):
        self.triggerPageAction(QWebEnginePage.SavePage)

    def _copyImageToClipboard(self):
        self.triggerPageAction(QWebEnginePage.CopyImageToClipboard)

    def _downloadLinkToDisk(self):
        self.triggerPageAction(QWebEnginePage.DownloadLinkToDisk)

    def _downloadImageToDisk(self):
        self.triggerPageAction(QWebEnginePage.DownloadImageToDisk)

    def _downloadMediaToDisk(self):
        self.triggerPageAction(QWebEnginePage.DownloadMediaToDisk)

    def _openActionUrl(self):
        action = self.sender()
        if isinstance(action, QAction):
            self.loadByUrl(action.data().toUrl())

    def _showSiteInfo(self):
        s = SiteInfo(self)
        s.show()

    def _searchSelectedText(self):
        pass

    def _searchSelectedTextInBackgroundTab(self):
        pass

    def _bookmarkLink(self):
        pass

    def _openUrlInSelectedTab(self):
        action = self.sender()
        if isinstance(action, QAction):
            self.openUrlInNewTab(action.data().toUrl(), const.NT_CleanSelectedTab)

    def _openUrlInBackgroundTab(self):
        action = self.sender()
        if isinstance(action, QAction):
            self.openUrlInNewTab(action.data().toUrl(), const.NT_CleanNotSelectedTab)

    # To support user's option whether to open in selected or background tab
    def userDefinedOpenUrlInNewTab(self, url=QUrl(), invert=False):
        pass

    def userDefineOpenUrlInBgTab(self, url=QUrl()):
        pass

    # protected:
    # override
    def showEvent(self, event):
        '''
        @param: event QShowEvent
        '''
        super().showEvent(event)
        pass

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super().resizeEvent(event)
        pass

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass

    # override
    def focusNextPrevChild(self, next_):
        '''
        @param: next_ bool
        '''
        return super().focusNextPrevChild(next_)

    # virtual method
    def _wheelEvent(self, event):
        '''
        @param: event QWheelEvent
        '''
        pass

    # virtual method
    def _mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # virtual method
    def _mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # virtual method
    def _mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # virtual method
    def _keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass

    # virtual method
    def _keyReleaseEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass

    # virtual method
    def _contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass

    def _loadRequest(self, req):
        '''
        @param: req LoadRequest
        '''
        super().load(req.webRequest())

    def _applyZoom(self):
        zoomFactor = self.zoomLevels()[self._currentZoomLevel] / 100
        self.setZoomFactor(zoomFactor)

        self.zoomLevelChanged.emit(self._currentZoomLevel)

    def _createContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        pass

    def _createPageContextMenu(self, menu):
        '''
        @param: menu QMenu
        '''
        pass

    def _createLinkContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        pass

    def _createImageContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        pass

    def _createSelectedTextContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        pass

    def _createMediaContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        pass

    def _checkForForm(self, action, pos):
        '''
        @param: action QAction
        @param: pos QPoint
        '''
        pass

    def _createSearchEngine(self):
        '''
        @return: void
        '''
        pass

    # Q_SLOTS
    def _addSpeedDial(self):
        pass

    def _configureSpeedDial(self):
        pass

    def _reloadAllSpeedDials(self):
        pass

    def _toggleMediaPause(self):
        pass

    def _toggleMediaMute(self):
        pass

    # private:
    def _initializeActions(self):
        pass
