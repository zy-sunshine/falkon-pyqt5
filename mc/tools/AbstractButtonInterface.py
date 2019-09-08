from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIcon
from mc.webengine.WebView import WebView

class AbstractButtonInterface(QObject):

    class ClickController:
        def __init__(self):
            self.visualParent = None
            self.popupPosition = None  # std::function<QPoint(QSize)>
            self.popupOpened = False
            self.popupClosed = None  # std::function<void()>

        def callPopupPosition(self, size):
            return self.popupPosition(size)

        def callPopupClosed(self):
            return self.popupClosed()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = True
        self._visible = True
        self._title = ''
        self._toolTip = ''
        self._icon = QIcon()
        self._badgeText = ''
        self._view = None

    def id(self):
        raise NotImplementedError

    def name(self):
        raise NotImplementedError

    def isValid(self):
        return self.id() and self.name()

    def isActive(self):
        return self._active

    def setActive(self, active):
        if self._active == active:
            return

        self._active = active
        self.activeChanged.emit(self._active)

    def isVisible(self):
        return self._visible

    def setVisible(self, visible):
        if self._visible == visible:
            return

        self._visible = visible
        self.visibleChanged.emit(self._visible)

    def title(self):
        return self._title

    def setTitle(self, title):
        if self._title == title:
            return

        self._title = title
        self.titleChanged.emit(self._title)

    def toolTip(self):
        return self._toolTip

    def setToolTip(self, toolTip):
        if self._toolTip == toolTip:
            return

        self._toolTip = toolTip
        self.toolTipChanged.emit(self._toolTip)

    def icon(self):
        '''
        @return: QIcon
        '''
        return self._icon

    def setIcon(self, icon):
        '''
        @param: icon QIcon
        '''
        self._icon = icon
        self.iconChanged.emit(icon)

    def badgeText(self):
        '''
        @return: QString
        '''
        return self._badgeText

    def setBadgeText(self, badgeText):
        '''
        @param: badgeText QString
        '''
        if self._badgeText == badgeText:
            return

        self._badgeText = badgeText
        self.badgeTextChanged.emit(self._badgeText)

    def webView(self):
        '''
        @return: WebView
        '''
        return self._view

    def setWebView(self, view):
        '''
        @param: view WebView
        '''
        if self._view == view:
            return

        self._view = view
        self.webViewChanged.emit(self._view)

    # public Q_SIGNALS:
    activeChanged = pyqtSignal(bool)  # active
    visibleChanged = pyqtSignal(bool)  # visible
    titleChanged = pyqtSignal(str)  # title
    toolTipChanged = pyqtSignal(str)  # toolTip
    iconChanged = pyqtSignal(QIcon)  # icon
    badgeTextChanged = pyqtSignal(str)  # badgeText
    webViewChanged = pyqtSignal(WebView)  # view
    clicked = pyqtSignal(ClickController)  # controller
