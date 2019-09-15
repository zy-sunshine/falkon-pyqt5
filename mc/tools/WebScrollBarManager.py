from PyQt5.Qt import QObject

class ScrollBarData:
    def __init__(self):
        self.vscrollbar = None  # WebScrollBar
        self.hscrollbar = None  # WebScrollBar
        self.vscrollbarVisible = False
        self.hscrollbarVisible = False
        self.corner = None  # WebScrollBarCornerWidget

class WebScrollBarManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._enable = False
        self._scrollbarJs = ''
        self._scrollbars = {}  # QHash<WebView*, struct ScrollBarData*>

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
        @param: orientation Qt.Orientation
        @param: view WebView
        '''
        pass

    # private:
    def _createUserScript(self, thickness):
        '''
        @param: thickness int
        '''
        pass

    def _removeUserScript(self):
        pass

    def _viewportSize(self, view, thickness):
        '''
        @param: view WebView
        @param: thickness int
        '''
        pass
