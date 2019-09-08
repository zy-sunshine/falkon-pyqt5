from .Plugins import Plugins
from mc.webengine.WebPage import WebPage
from mc.app.BrowserWindow import BrowserWindow
from PyQt5.Qt import pyqtSignal

class PluginProxy(Plugins):
    # enum EnventHandlerType
    MouseDoubleClickHandler = 0
    MousePressHandler = 1
    MouseReleaseHandler = 2
    MouseMoveHandler = 3
    KeyPressHandler = 4
    KeyReleaseHandler = 5
    WheelEventHandler = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouseDoubleClickHandlers = []  # QList<PluginInterface>
        self._mousePressHandlers = []  # QList<PluginInterface>
        self._mouseReleaseHandlers = []  # QList<PluginInterface>
        self._mouseMoveHandlers = []  # QList<PluginInterface>

        self._wheelEventHandlers = []  # QList<PluginInterface>

        self._keyPressHandlers = []  # QList<PluginInterface>
        self._keyReleaseHandlers = []  # QList<PluginInterface>

    def registerAppEventHandler(self, type_, obj):
        '''
        @param: type_ EventHandlerType
        @param: obj PluginInterface
        '''
        pass

    def populateWebViewMenu(self, menu, view, r):
        '''
        @param: menu QMenu
        @param: view WebView
        @param: r WebHitTestResult
        '''
        pass

    def populateExtensionsMenu(self, menu):
        '''
        @param: menu QMenu
        '''
        pass

    def processMouseDoubleClick(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QMouseEvent
        @return: bool
        '''
        pass

    def processMousePress(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QMouseEvent
        @return: bool
        '''
        pass

    def processMouseRelease(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QMouseEvent
        @return: bool
        '''
        pass

    def processMouseMove(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QMouseEvent
        @return: bool
        '''
        pass

    def processWheelEvent(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QWheelEvent
        @return: bool
        '''
        pass

    def processKeyPress(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QKeyEvent
        @return: bool
        '''
        pass

    def processKeyRelease(self, type_, obj, event):
        '''
        @param: type_ const.ObjectName
        @param: obj QObject
        @param: event QKeyEvent
        @return: bool
        '''
        pass

    def acceptNavigationRequest(self, page, url, type_, isMainFrame):
        '''
        @param: page WebPage
        @param: url QUrl
        @param: type_ QWebEnginePage.NavigationType
        @param: isMainFrame
        @return: bool
        '''
        pass

    def emitWebPageCreated(self, page):
        '''
        @param: page WebPage
        '''
        pass

    def emitWebPageDeleted(self, page):
        '''
        @param: page WebPage
        '''
        pass

    def emitMainWindowCreated(self, window):
        '''
        @param: window BrowserWindow*
        '''
        pass

    def emitMainWindowDeleted(self, window):
        '''
        @param: window BrowserWindow*
        '''
        pass

    # Q_SIGNALS:
    webPageCreated = pyqtSignal(WebPage)  # page
    webPageDeleted = pyqtSignal(WebPage)  # page
    mainWindowCreated = pyqtSignal(BrowserWindow)  # window
    mainWindowDeleted = pyqtSignal(BrowserWindow)  # window

    # private QSLOTS:
    def _pluginUnloaded(self, plugin):
        '''
        @param: plugin PluginInterface
        '''
        pass
