from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.Qt import QSize

class WebInspector(QWebEngineView):

    s_views = []  # QList<QWebEngineView*>
    def __init__(self, parent=None):
        super().init(parent)
        self._height = 0
        self._windowSize = QSize()
        self._inspectElement = False
        self._view = None  # WebView

    def setView(self, view):
        pass

    def inspectElement(self):
        pass

    # override
    def sizeHint(self):
        pass

    @classmethod
    def isEnabled(cls):
        return False

    @classmethod
    def pushView(cls, view):
        '''
        @param: view QWebEngineView
        '''
        pass

    @classmethod
    def registerView(self, view):
        '''
        @param: view QWebEngineView
        '''
        pass

    @classmethod
    def unregisterView(self, view):
        '''
        @param: view QWebEngineView
        '''
        pass

    # private Q_SLOTS:
    def _loadFinished(self):
        pass

    # private:
    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass

    # override
    def keyReleaseEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass
