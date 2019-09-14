from mc.webengine.WebView import WebView
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from mc.tools.EnhancedMenu import Menu

class TabbedWebView(WebView):
    def __init__(self, webTab):
        '''
        @param: webTab WebTab
        '''
        super(TabbedWebView, self).__init__(webTab)
        self._window = None  # BrowserWindow
        self._webTab = webTab  # WebTab
        self._menu = Menu(self)  # Menu

        self._currentIp = ''

        self._menu.setCloseOnMiddleClick(True)

        self.loadStarted.connect(self._slotLoadStarted)
        self.loadProgress.connect(self._slotLoadProgress)
        self.loadFinished.connect(self._slotLoadFinished)

    def setPage(self, page):
        '''
        @param: page WebPage
        '''
        super(TabbedWebView, self).setPage(page)
        page.linkHovered.connect(self._linkHovered)

    def browserWindow(self):
        '''
        @note: BrowserWindow can be null!
        @return: BrowserWindow
        '''
        return self._window

    def setBrowserWindow(self, window):
        self._window = window

    def webTab(self):
        '''
        @return: WebTab
        '''
        return self._webTab

    def getIp(self):
        '''
        @return: QString
        '''
        return self._currentIp

    def tabIndex(self):
        '''
        @return int
        '''
        return self._webTab.tabIndex()

    # override
    def overlayWidget(self):
        '''
        @return: QWidget
        '''
        import ipdb; ipdb.set_trace()
        return self._webTab

    # override
    def closeView(self):
        self.wantsCloseTab.emit(self.tabIndex())

    # override
    def loadInNewTab(self, req, position):
        '''
        @param: req LoadRequest
        @param: position Qz::NewTabPositionFlags
        '''
        if self._window:
            index = self._window.tabWidget().addViewByUrl(QUrl(), position)
            view = self._window.weView(index)
            self.webTab().addChildTab(view.webTab())
            view.webTab().locationBar().showUrl(req.url())
            view.loadByReq(req)

    # override
    def isFullScreen(self):
        return self._window and self._window.isFullScreen()

    # override
    def requestFullScreen(self, enable):
        if not self._window:
            return

        self._window.requestHtmlFullScreen(self, enable)

    # Q_SIGNALS
    wantsCloseTab = pyqtSignal(int)
    ipChanged = pyqtSignal(str)

    # public Q_SLOTS
    def setAsCurrentTab(self):
        if self._window:
            self._window.tabWidget().setCurrentWidget(self._webTab)

    def userLoadAction(self, req):
        '''
        @param: req LoadRequest
        '''
        self.loadByReq(req)

    # private Q_SLOTS
    def _slotLoadStarted(self):
        self._currentIp = ''

    def _slotLoadFinished(self, ok):
        pass

    def _slotLoadProgress(self, prog):
        '''
        @param: prog int
        '''
        if self._webTab.isCurrentTab() and self._window:
            self._window.updateLoadingActions()

    def _linkHovered(self, link):
        '''
        @param: QString
        '''
        if self._webTab.isCurrentTab() and self._window:
            if not link:
                self._window.statusBar().clearMessage()
            else:
                self._window.statusBar().showMessage(link)

    def _setIp(self, info):
        '''
        @param: info QHostInfo
        '''
        pass

    def _inspectElement(self):
        pass

    # private:
    # override
    def _contextMenuEvent(self, event):
        '''
        @param: QContextMenuEvent
        '''
        pass

    # override
    def _mouseMoveEvent(self, event):
        '''
        @param: QMouseEvent
        '''
        pass
