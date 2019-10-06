from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.Qt import pyqtSignal, pyqtSlot
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
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QIcon
from PyQt5.Qt import QContextMenuEvent
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QChildEvent
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5 import sip

from .WebPage import WebPage
from mc.tools.WheelHelper import WheelHelper
from mc.common.globalvars import gVar
from .WebInspector import WebInspector
from .WebScrollBarManager import WebScrollBarManager
from mc.tools.IconProvider import IconProvider
from mc.common import const
from mc.other.SiteInfo import SiteInfo
from mc.tools.EnhancedMenu import Action, Menu
from mc.webengine.LoadRequest import LoadRequest
from mc.opensearch.SearchEnginesManager import SearchEngine
from mc.bookmarks.BookmarksTools import BookmarksTools

class WebView(QWebEngineView):
    _s_forceContextMenuOnMouseRelease = False

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

        self.loadStarted.connect(lambda: WebView._slotLoadStarted(self))
        self.loadProgress.connect(lambda progress: WebView._slotLoadProgress(self, progress))
        self.loadFinished.connect(lambda ok: WebView._slotLoadFinished(self, ok))
        self.iconChanged.connect(lambda: WebView._slotIconChanged(self))
        self.urlChanged.connect(lambda url: WebView._slotUrlChanged(self, url))
        self.titleChanged.connect(lambda title: WebView._slotTitleChanged(self, title))

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
        #self._initializeActions()

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
        print('eventFilter')
        evtype = event.type()
        # Keyboard events are sent to parent widget
        if obj == self and evtype == QEvent.ParentChange and self.parentWidget():
            self.parentWidget().installEventFilter(self)

        # Hack to find widget that receives input events
        if obj == self and evtype == QEvent.ChildAdded:
            if const.QTWEBENGINEWIDGETS_VERSION >= const.QT_VERSION_CHECK(5, 12, 0):
                # NOTE: qobject_cast<QWidget*>(static_cast<QChildEvent*>(event)->child());
                assert(isinstance(event, QChildEvent))
                child = event.child()
                #assert(isinstance(child, QWidget))

                def xxx():
                    if not sip.isdeleted(child) and \
                            child.inherits('QWebEngineCore::RenderWidgetHostViewQtDelegateWidget'):
                        self._rwhvqt = child
                        self._rwhvqt.installEvent(self)
                        w = self._rwhvqt
                        if isinstance(w, QQuickWidget):
                            w.setClearColor(self.palette().color(QPalette.Window))
                QTimer.singleShot(0, xxx)
            else:
                def yyy():
                    focusProxy = self.focusProxy()
                    if focusProxy and self._rwhvqt != focusProxy:
                        self._rwhvqt = focusProxy
                        self._rwhvqt.installEventFilter(self)
                        w = self._rwhvqt
                        if isinstance(w, QQuickWidget):
                            w.setClearColor(self.palette().color(QPalette.Window))
                QTimer.singleShot(0, yyy)

        def _HANDLE_EVENT(f, t):
            wasAccepted = event.isAccepted()
            event.setAccepted(False)
            f(event)
            ret = event.isAccepted()
            event.setAccepted(wasAccepted)
            return ret
        # Forward events to WebView
        if obj == self._rwhvqt:
            if evtype == QEvent.MouseButtonPress:
                return _HANDLE_EVENT(self._mousePressEvent, QMouseEvent)
            elif evtype == QEvent.MouseButtonRelease:
                return _HANDLE_EVENT(self.mouseReleaseEvent, QMouseEvent)
            elif evtype == QEvent.MouseMove:
                return _HANDLE_EVENT(self.mouseMoveEvent, QMouseEvent)
            elif evtype == QEvent.Wheel:
                return _HANDLE_EVENT(self._wheelEvent, QWheelEvent)

        if obj == self.parentWidget():
            if evtype == QEvent.KeyPress:
                return _HANDLE_EVENT(self._keyPressEvent, QKeyEvent)
            if evtype == QEvent.KeyRelease:
                return _HANDLE_EVENT(self._keyReleaseEvent, QKeyEvent)

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
        import ipdb; ipdb.set_trace()
        self.triggerPageAction(QWebEnginePage.Undo)

    def editRedo(self):
        import ipdb; ipdb.set_trace()
        self.triggerPageAction(QWebEnginePage.Redo)

    def editCut(self):
        import ipdb; ipdb.set_trace()
        self.triggerPageAction(QWebEnginePage.Cut)

    def editCopy(self):
        import ipdb; ipdb.set_trace()
        self.triggerPageAction(QWebEnginePage.Copy)

    def editPaste(self):
        import ipdb; ipdb.set_trace()
        self.triggerPageAction(QWebEnginePage.Paste)

    def editSelectAll(self):
        self.triggerPageAction(QWebEnginePage.SelectAll)

    def editDelete(self):
        import ipdb; ipdb.set_trace()
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
            return

        self.triggerPageAction(QWebEnginePage.ViewSource)

    def sendPageByEmail(self):
        body = QUrl.toPercentEncoding(self.url().toEncoded().data().decode())
        subject = QUrl.toPercentEncoding(self.title())
        mailUrl = QUrl.fromEncoded(b'mailto:%%20?body=%s&subject=%s' % (body, subject))
        QDesktopServices.openUrl(mailUrl)

    def openUrlInNewTab(self, url, position):
        '''
        @param: url QUrl
        @param: position Qz::NewTabPositionFlags
        '''
        self.loadInNewTab(LoadRequest(url), position)

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
            gVar.app.createWindow(const.BW_NewWindow, action.data())

    def _sendTextByMail(self):
        action = self.sender()
        if isinstance(action, QAction):
            data = action.data()
            if isinstance(data, QByteArray):
                data = data.data().decode()
            body = QUrl.toPercentEncoding(data)
            mailUrl = QUrl.fromEncoded(b'mailto:%%20?body=%s' % body)
            QDesktopServices.openUrl(mailUrl)

    def _copyLinkToClipboard(self):
        action = self.sender()
        if isinstance(action, QAction):
            QApplication.clipboard().setText(action.data().toEncoded().data().decode())

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
            self.loadByUrl(action.data())

    def _showSiteInfo(self):
        s = SiteInfo(self)
        s.show()

    def _searchSelectedText(self):
        engine = gVar.app.searchEnginesManager().defaultEngine()
        act = self.sender()
        if isinstance(act, QAction):
            data = act.data()
            if data and isinstance(data, SearchEngine):
                engine = data

        # LoadRequest
        req = gVar.app.searchEnginesManager().searchResult(engine, self.selectedText())
        self.loadInNewTab(req, const.NT_SelectedTab)

    def _searchSelectedTextInBackgroundTab(self):
        engine = gVar.app.searchEnginesManager().defaultEngine()
        act = self.sender()
        if isinstance(act, QAction):
            data = act.data()
            if data and isinstance(data, SearchEngine):
                engine = data

        # LoadRequest
        req = gVar.app.searchEnginesManager().searchResult(engine, self.selectedText())
        self.loadInNewTab(req, const.NT_NotSelectedTab)

    def _bookmarkLink(self):
        action = self.sender()
        if isinstance(action, QAction):
            data = action.data()
            if not data:
                BookmarksTools.addBookmarkDialog(self, self.url(), self.title())
            elif type(data) in (list, tuple):
                url = QUrl(data[0])
                title = data[1]
                if not title:
                    title = self.title()

                BookmarksTools.addBookmarkDialog(self, url, title)

    def _openUrlInSelectedTab(self):
        action = self.sender()
        if isinstance(action, QAction):
            self.openUrlInNewTab(action.data(), const.NT_CleanSelectedTab)

    def _openUrlInBackgroundTab(self):
        action = self.sender()
        if isinstance(action, QAction):
            self.openUrlInNewTab(action.data(), const.NT_CleanNotSelectedTab)

    # To support user's option whether to open in selected or background tab
    def userDefinedOpenUrlInNewTab(self, url=QUrl(), invert=False):
        position = gVar.appSettings.newTabPosition
        if invert:
            if position & const.NT_SelectedTab:
                position &= ~const.NT_SelectedTab
                position |= const.NT_NotSelectedTab
            else:
                position &= ~const.NT_NotSelectedTab
                position |= const.NT_SelectedTab

        actionUrl = QUrl()

        if not url.isEmpty():
            actionUrl = url
        else:
            action = self.sender()
            if isinstance(action, QAction):
                actionUrl = action.data()

        self.openUrlInNewTab(actionUrl, position)

    def userDefineOpenUrlInBgTab(self, url=QUrl()):
        actionUrl = QUrl()

        if not url.isEmpty():
            actionUrl = url
        else:
            action = self.sender()
            if isinstance(action, QAction):
                actionUrl = action.data()

        self.userDefinedOpenUrlInNewTab(actionUrl, True)

    # protected:
    # override
    def showEvent(self, event):
        '''
        @param: event QShowEvent
        '''
        super().showEvent(event)

        if self._backgroundActivity:
            self._backgroundActivity = False
            self.backgroundActivityChanged.emit(self._backgroundActivity)

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super().resizeEvent(event)
        self.viewportResized.emit(self.size())

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        # Context menu is created in mouseReleaseEvent
        if self._s_forceContextMenuOnMouseRelease:
            return

        # QPoint
        pos = event.pos()
        # QContextMenuEvent::Reason
        reason = event.reason()

        def contextMenuEventCb():
            event = QContextMenuEvent(reason, pos)
            self._contextMenuEvent(event)
        QTimer.singleShot(0, contextMenuEventCb)

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

    def _createContextMenu(self, menu, hitTest):  # noqa C901
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        spellCheckActionCount = 0

        # QWebEngineContextMenuData
        contextMenuData = self.page().contextMenuData()
        hitTest.updateWithContextMenuData(contextMenuData)

        if contextMenuData.misspelledWord():
            boldFont = menu.font()
            boldFont.setBold(True)

            for suggestion in contextMenuData.spellCheckerSuggestions():
                action = menu.addAction(suggestion)
                action.setFont(boldFont)

                def sugCb():
                    self.page().replaceMisspelledWord(suggestion)
                action.triggered.connect(sugCb)

            if not menu.actions():
                menu.addAction(_('No suggestions')).setEnabled(False)

            menu.addSeparator()
            spellCheckActionCount = len(menu.actions())

        if not hitTest.linkUrl().isEmpty() and hitTest.linkUrl().scheme() != 'javascript':
            self._createLinkContextMenu(menu, hitTest)

        if not hitTest.imageUrl().isEmpty():
            self._createImageContextMenu(menu, hitTest)

        if not hitTest.mediaUrl().isEmpty():
            self._createMediaContextMenu(menu, hitTest)

        if hitTest.isContentEditable():
            # This only checks if the menu is empty (only spellchecker actions added)
            if len(menu.actions()) == spellCheckActionCount:
                self._addPageActionToMenu(menu, QWebEnginePage.Undo)
                self._addPageActionToMenu(menu, QWebEnginePage.Redo)
                menu.addSeparator()
                self._addPageActionToMenu(menu, QWebEnginePage.Cut)
                self._addPageActionToMenu(menu, QWebEnginePage.Copy)
                self._addPageActionToMenu(menu, QWebEnginePage.Paste)

            if hitTest.tagName() == 'input':
                act = menu.addAction('')
                act.setVisible(False)
                self._checkForForm(act, hitTest.pos())

        if self.selectedText():
            self._createSelectedTextContextMenu(menu, hitTest)

        if menu.isEmpty():
            self._createPageContextMenu(menu)

        menu.addSeparator()
        # TODO:
        # gVar.app.plugins().populateWebViewMenu(menu, self, hitTest)

    def _createPageContextMenu(self, menu):
        '''
        @param: menu QMenu
        '''
        action = menu.addAction(_('&Back'), self.back)
        action.setIcon(IconProvider.standardIcon(QStyle.SP_ArrowBack))
        action.setEnabled(self.history().canGoBack())

        action = menu.addAction(_('&Forward'), self.forward)
        action.setIcon(IconProvider.standardIcon(QStyle.SP_ArrowForward))
        action.setEnabled(self.history().canGoForward())

        # Special menu for Speed Dial page
        if self.url().toString() == 'app:speeddial':
            menu.addSeparator()
            menu.addAction(QIcon.fromTheme('list-add'), _('&Add New Page'),
                    self._addSpeedDial)
            menu.addAction(IconProvider.settingsIcon(), _('&Configure Speed Dial'),
                    self._configureSpeedDial)
            menu.addSeparator()
            menu.addAction(QIcon.fromTheme('view-refresh'), _('Reload All Dials'),
                    self._reloadAllSpeedDials)
            return

        reloadAct, pageReloadAct = self._addPageActionToMenu(menu, QWebEnginePage.Reload)
        reloadAct.setVisible(pageReloadAct.isEnabled())

        def reloadCb():
            reloadAct.setVisible(pageReloadAct.isEnabled())
        pageReloadAct.changed.connect(reloadCb)
        menu.clearActions.append([pageReloadAct.changed, reloadCb])

        stopAct, pageStopAct = self._addPageActionToMenu(menu, QWebEnginePage.Stop)
        stopAct.setVisible(pageStopAct.isEnabled())

        def stopCb():
            stopAct.setVisible(pageStopAct.isEnabled())
        pageStopAct.changed.connect(stopCb)
        menu.clearActions.append([pageStopAct.changed, stopCb])

        menu.addSeparator()
        menu.addAction(QIcon.fromTheme('bookmark-new'), _('Book&mark page'), self._bookmarkLink)
        menu.addAction(QIcon.fromTheme('document-save'), _('&Save page as...'), self._savePageAs)
        act = menu.addAction(QIcon.fromTheme('edit-copy'), _('&Copy page link...'), self._copyLinkToClipboard)
        act.setData(self.url())
        menu.addAction(QIcon.fromTheme('mail-message-new'), _('Send page link...'), self.sendPageByEmail)
        menu.addSeparator()
        menu.addAction(QIcon.fromTheme('edit-select-all'), _('Select &all'), self.editSelectAll)
        menu.addSeparator()

    def _createLinkContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        menu.addSeparator()
        act = Action(IconProvider.newTabIcon(), _('Open link in new &tab'), menu)
        act.setData(hitTest.linkUrl())
        act.triggered.connect(lambda: self.userDefinedOpenUrlInNewTab())
        act.ctrlTriggered.connect(lambda: self.userDefineOpenUrlInBgTab())
        menu.addAction(act)
        act = menu.addAction(IconProvider.newWindowIcon(), _('Open link in new &window'),
                self._openUrlInNewWindow)
        act.setData(hitTest.linkUrl())
        act = menu.addAction(IconProvider.privateBrowsingIcon(), _('Open link in &private window'),
                gVar.app.startPrivateBrowsing)
        act.setData(hitTest.linkUrl())
        menu.addSeparator()

        bData = [hitTest.linkUrl(), hitTest.linkTitle()]  # QVariantList
        act = menu.addAction(QIcon.fromTheme('bookmark-new'), _('B&ookmark link'),
            self._bookmarkLink)
        act.setData(bData)

        menu.addAction(QIcon.fromTheme('document-save'), _('&Save link as...'),
                self._downloadLinkToDisk)
        act = menu.addAction(QIcon.fromTheme('mail-message-new'), _('Send link...'),
                self._sendTextByMail)
        act.setData(hitTest.linkUrl().toEncoded())
        act = menu.addAction(QIcon.fromTheme('edit-copy'), _('&Copy link address'),
                self._copyLinkToClipboard)
        act.setData(hitTest.linkUrl())
        menu.addSeparator()

        if self.selectedText():
            menu.addAction(self.pageAction(QWebEnginePage.Copy))

    def _createImageContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        menu.addSeparator()
        if hitTest.imageUrl() != self.url():
            act = Action(_('Show i&mage'), menu)
            act.setData(hitTest.imageUrl())
            act.triggered.connect(self._openActionUrl)
            act.ctrlTriggered.connect(lambda: self.userDefinedOpenUrlInNewTab())
            menu.addAction(act)
        menu.addAction(_('Copy image'), self._copyImageToClipboard)
        act = menu.addAction(QIcon.fromTheme('edit-copy'), _('Copy image ad&dress'),
                self._copyLinkToClipboard)
        act.setData(hitTest.imageUrl())
        menu.addSeparator()
        menu.addAction(QIcon.fromTheme('document-save'), _('&Save image as...'),
                self._downloadImageToDisk)
        act = menu.addAction(QIcon.fromTheme('mail-message-new'), _('Send image...'),
                self._sendTextByMail)
        act.setData(hitTest.imageUrl().toEncoded())
        menu.addSeparator()

        if self.selectedText():
            menu.addAction(self.pageAction(QWebEnginePage.Copy))

    def _createSelectedTextContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        selectedText = self.page().selectedText()

        menu.addSeparator()
        if self.pageAction(QWebEnginePage.Copy) not in menu.actions():
            menu.addAction(self.pageAction(QWebEnginePage.Copy))
        menu.addAction(QIcon.fromTheme('mail-message-new'), _('Send text...'),
                self._sendTextByMail).setData(selectedText)
        menu.addSeparator()

        # 379: Remove newlines
        selectedString = selectedText.strip()
        if '.' not in selectedString:
            # Try to add .com
            selectedString += '.com'
        guessedUrl = QUrl.fromUserInput(selectedString)
        if self.isUrlValid(guessedUrl):
            act = Action(QIcon.fromTheme('document-open-remote'), _('Go to &web address'), menu)
            act.setData(guessedUrl)

            act.triggered.connect(self._openActionUrl)
            act.ctrlTriggered.connect(lambda: self.userDefinedOpenUrlInNewTab())
            menu.addAction(act)

        menu.addSeparator()
        selectedText = selectedText[:20]
        # KDE is displaying newlines in menu actions ... weird
        selectedText = selectedText.replace('\n', ' ').replace('\t', ' ')

        engine = gVar.app.searchEnginesManager().defaultEngine()
        act = Action(engine.icon, _('Search "%s .." with %s') % (selectedText, engine.name), menu)
        act.triggered.connect(self._searchSelectedText)
        act.ctrlTriggered.connect(self._searchSelectedTextInBackgroundTab)
        menu.addAction(act)

        # Search with ...
        swMenu = Menu(_('Search with...'), menu)
        swMenu.setCloseOnMiddleClick(True)
        searchManager = gVar.app.searchEnginesManager()
        for en in searchManager.allEngines():
            act = Action(en.icon, en.name, swMenu)
            act.setData(en)

            act.triggered.connect(self._searchSelectedText)
            act.ctrlTriggered.connect(self._searchSelectedTextInBackgroundTab)
            swMenu.addAction(act)

        menu.addMenu(swMenu)

    def _createMediaContextMenu(self, menu, hitTest):
        '''
        @param: menu QMenu
        @param: hitTest WebHitTestResult
        '''
        paused = hitTest.mediaPaused()
        muted = hitTest.mediaMuted()

        menu.addSeparator()
        act = menu.addAction(paused and _('&Paly') or _('&Pause'), self._toggleMediaPause)
        act.setIcon(QIcon.fromTheme(paused and 'media-playback-start' or 'media-playback-pause'))
        act = menu.addAction(muted and _('Un&mute') or _('&Mute'), self._toggleMediaMute)
        act.setIcon(QIcon.fromTheme(muted and 'audio-volume-muted' or 'audio-volume-high'))
        menu.addSeparator()
        act = menu.addAction(QIcon.fromTheme('edit-copy'), _('&Copy Media Address'), self._copyLinkToClipboard)
        act.setData(hitTest.mediaUrl())
        act = menu.addAction(QIcon.fromTheme('mail-message-new'), _('&Send Media Address'), self._sendTextByMail)
        act.setData(hitTest.mediaUrl().toEncoded())
        menu.addAction(QIcon.fromTheme('document-save'), _('Save Media To &Disk'), self._downloadMediaToDisk)

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
        self.triggerPageAction(QWebEnginePage.ToggleMediaPlayPause)

    def _toggleMediaMute(self):
        self.triggerPageAction(QWebEnginePage.ToggleMediaMute)

    # private:
    def _initializeActions(self):
        for type_, text, shortcut, useCtx, theme in [
            (QWebEnginePage.Undo, _('&Undo'), 'Ctrl+Z', True, 'edit-undo'),
            (QWebEnginePage.Redo, _('&Redo'), 'Ctrl+Shift+Z', True, 'edit-redo'),
            (QWebEnginePage.Cut, _('&Cut'), 'Ctrl+X', True, 'edit-cut'),
            (QWebEnginePage.Copy, _('&Copy'), 'Ctrl+C', True, 'edit-copy'),
            (QWebEnginePage.Paste, _('&Paste'), 'Ctrl+V', True, 'edit-paste'),
            (QWebEnginePage.SelectAll, _('Select All'), 'Ctrl+A', True, 'edit-select-all'),

            (QWebEnginePage.Reload, _('&Reload'), '', False, 'view-refresh'),
            (QWebEnginePage.Stop, _('S&top'), '', False, 'process-stop'),
        ]:
            act = self.pageAction(type_)
            act.setText(text)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            if useCtx:
                act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            if not useCtx:
                self.addAction(act)
            act.setIcon(QIcon.fromTheme(theme))

    def _addPageActionToMenu(self, menu, type_, icon=None):
        pageAct = self.pageAction(type_)
        if icon is not None:
            pageAct.setIcon(icon)
        act = menu.addAction(pageAct.icon(), pageAct.text(), pageAct.trigger)
        return act, pageAct
