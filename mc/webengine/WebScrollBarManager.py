from PyQt5.Qt import QObject

class WebScrollBarManager(QObject):

    __instance = None
    def __init__(self, parent=None):
        self._enabled = True
        self._scrollbarJs = ''
        self._scrollbars = {}  # QHash<WebView*, struct ScrollBarData*>

    @classmethod
    def instance(cls):
        if cls.__instance is None:
            cls.__instance = WebScrollBarManager()
        return cls.__instance

    def loadSettings(self):
        pass

    def addWebView(self, view):
        '''
        @param: view WebView
        '''
        pass

    def removeWebView(self, view):
        '''
        @param: view WebView
        '''
        pass

    def scrollBar(self, orientation, view):
        '''
        @param: orientation Qt::Orienttation
        @param: view WebView
        @return: QScrollBar
        '''
        pass

    # private:
    def _createUserScript(self, thickness):
        pass

    def _removeUserScript(self):
        pass

    def _viewportSize(self, view, thickness):
        '''
        @param: view WebView
        @param: thickness int
        @return: QSize
        '''
        pass
