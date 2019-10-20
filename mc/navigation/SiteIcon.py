from mc.tools.ToolButton import ToolButton
from PyQt5.Qt import Qt, QPoint, QIcon, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QDrag, QMimeData
from mc.common.globalvars import gVar
from mc.other.SiteInfo import SiteInfo
from mc.other.SiteInfoWidget import SiteInfoWidget

class SiteIcon(ToolButton):
    def __init__(self, parent):
        '''
        @param: parent LocationBar
        '''
        super().__init__(parent)
        self._window = None  # BrowserWindow
        self._locationBar = parent  # LocationBar
        self._view = None  # WebView
        self._updateTimer = None  # QTimer

        self._drawStartPosition = QPoint()
        self._icon = QIcon()

        self.setObjectName('locationbar-siteicon')
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setCursor(Qt.ArrowCursor)
        self.setToolTip(_('Show information about this page'))
        self.setFocusPolicy(Qt.NoFocus)

        self._updateTimer = QTimer(self)
        self._updateTimer.setInterval(100)
        self._updateTimer.setSingleShot(True)
        self._updateTimer.timeout.connect(self._updateIcon)

    def setBrowserWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._window = window

    def setWebView(self, view):
        '''
        @param: view WebView
        '''
        self._view = view

    def setIcon(self, icon):
        '''
        @param: icon QIcon
        '''
        wasNull = self._icon.isNull()
        self._icon = icon
        if wasNull:
            self._updateIcon()
        else:
            self._updateTimer.start()

    # private Q_SLOTS:
    def _updateIcon(self):
        super().setIcon(self._icon)

    def _popupClosed(self):
        self.setDown(False)

    # private:
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        # Prevent propagating to LocationBar
        event.accept()

    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if event.buttons() == Qt.LeftButton:
            self._drawStartPosition = event.pos()

        # Prevent propagating to LocationBar
        event.accept()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        # Mouse release event is storing Down state
        # So we pause updates to prevent flicker

        activated = False
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            # Popup may not be always shown. eg. on app: pages
            activated = self._showPopup()

        if activated:
            self.setUpdatesEnabled(False)

        super().mouseReleaseEvent(event)

        if activated:
            self.setDown(False)
            self.setUpdatesEnabled(True)

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if not self._locationBar or event.buttons() != Qt.LeftButton:
            super().mouseMoveEvent(event)
            return

        manhattanLength = (event.pos() - self._drawStartPosition).manhattanLength()
        if manhattanLength <= QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        url = self._locationBar.webView().url()
        title = self._locationBar.webView().title()

        if url.isEmpty() or not title:
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setUrls([url])
        mime.setText(title)
        mime.setImageData(self.icon.pixmap(16).toImage())

        drag.setMimeData(mime)
        drag.setPixmap(gVar.appTools.createPixmapForSite(self.icon, title, url.toString()))
        drag.exec_()

        # Restore Down State
        self.setDown(False)

    def _showPopup(self):
        if not self._view or not self._window:
            return False

        url = self._view.url()

        if not SiteInfo.canShowSiteInfo(url):
            return False

        self.setDown(True)

        # SiteInfoWidget
        info = SiteInfoWidget(self._window)
        info.showAt(self.parentWidget())

        info.destroyed.connect(self._popupClosed)

        return True
