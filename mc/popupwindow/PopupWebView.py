from mc.webengine.WebView import WebView
from mc.tools.EnhancedMenu import Menu
from mc.common.globalvars import gVar
from mc.common import const
from mc.webengine.WebInspector import WebInspector
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.Qt import QPoint
from PyQt5.Qt import QUrl

class PopupWebView(WebView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._menu = Menu()  # Menu
        self._inspector = None  # QPoint<WebInspector>

        self._menu.setCloseOnMiddleClick(True)

    # override
    def overlayWidget(self):
        '''
        @return: QWidget
        '''
        return self.parentWidget()

    # override
    def loadInNewTab(self, req, position):
        '''
        @param: req LoadRequest
        @param: position Qz::NewTabPositionFlags
        '''
        window = gVar.app.getWindow()

        if window:
            index = window.tabWidget().addView(QUrl(), const.NT_SelectedTab)
            window.weView(index).loadByReq(req)
            window.raise_()

    # override
    def closeView(self):
        self.window().close()

    # override
    def isFullScreen(self):
        return self.parentWidget().isFullScreen()

    # override
    def requestFullScreen(self, enable):
        if enable:
            self.parentWidget().showFullScreen()
        else:
            self.parentWidget().showNormal()

    # public Q_SLOTS:
    def inspectElement(self):
        if not WebInspector.isEnabled():
            return

        if self._inspector:
            self.triggerPageAction(QWebEnginePage.InspectElement)
            return

        self._inspector = WebInspector()
        self._inspector.setView(self)
        self._inspector.inspectElement()
        self._inspector.show()

    # private:
    # override
    def _contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        self._menu.clear()

        # WebHitTestResult
        hitTest = self.page().hitTestContent(event.pos())
        self.createContextMenu(self._menu, hitTest)

        if WebInspector.isEnabled():
            self._menu.addSeparator()
            self._menu.addAction('Inspect Element', self.inspectElement)

        if not self._menu.isEmpty():
            # Prevent choosing first option with double rightclick
            pos = event.globalPos()
            p = QPoint(pos.x(), pos.y() + 1)

            self._menu.popup(p)
            return

        super()._contextMenuEvent(event)
