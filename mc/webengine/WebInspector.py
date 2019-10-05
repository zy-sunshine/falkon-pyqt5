from json import loads as jloads
from PyQt5.Qt import QSize
from PyQt5.Qt import Qt
from PyQt5.QtCore import qEnvironmentVariable
from PyQt5.Qt import QNetworkRequest
from PyQt5.Qt import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.app.Settings import Settings
from mc.common import const
from mc.common.globalvars import gVar

class WebInspector(QWebEngineView):

    _s_views = []  # QList<QWebEngineView*>
    def __init__(self, parent=None):
        super().__init__(parent)
        self._height = 0
        self._windowSize = QSize()
        self._inspectElement = False
        self._view = None  # WebView

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName('web-inspector')
        self.setMinimumHeight(80)

        self._height = Settings().value('Web-Inspector/height', 80)
        self._windowSize = Settings().value('Web-Inspector/windowSize', QSize(640, 480))

        self.registerView(self)

        self.page().windowCloseRequested.connect(self._onDestroyed)
        self.page().loadFinished.connect(self._loadFinished)
        #self.destroyed.connect(self._onDestroyed)

    def _onDestroyed(self):
        self.deleteLater()
        # TODO: check destroy can run these logics
        if self._view and self.hasFocus():
            self._view.setFocus()

        self.unregisterView(self)

        if self.isWindow():
            Settings().setValue('Web-Inspector/WindowSize', self.size())
        else:
            Settings().setValue('Web-Inspector/height', self.height())

    def setView(self, view):
        self._view = view
        assert(self.isEnabled())

        if const.QTWEBENGINEWIDGETS_VERSION >= const.QT_VERSION_CHECK(5, 11, 0):
            self.page().setInspectedPage(self._view.page())
            self._view.pageChanged.connect(self.deleteLater)
        else:
            port = qEnvironmentVariable('QTWEBENGINE_REMOTE_DEBUGGING')
            inspectorUrl = QUrl('http://localhost:%s' % port)
            index = self._s_views.index(self._view)

            reply = gVar.app.networkManager().get(QNetworkRequest(inspectorUrl.resolved(QUrl('json/list'))))

            def replyCb():
                clients = jloads(reply.readAll())
                pageUrl = QUrl()
                if len(clients) > index:
                    obj = clients[index]
                    pageUrl = inspectorUrl.resolved(QUrl(obj['devtoolsFrontendUrl']))
                self.load(pageUrl)
                self.pushView(self)
                self.show()

            reply.finished.connect(replyCb)

    def inspectElement(self):
        self._inspectElement = True

    # override
    def sizeHint(self):
        if self.isWindow():
            return self._windowSize()

        sz = super().sizeHint()
        sz.setHeight(self._height)
        return sz

    @classmethod
    def isEnabled(cls):
        if const.QTWEBENGINEWIDGETS_VERSION < const.QT_VERSION_CHECK(5, 11, 0):
            if qEnvironmentVariable('QTWEBENGINE_REMOTE_DEBUGGING') is None:
                return False
        if not gVar.app.webSettings().testAttribute(QWebEngineSettings.JavascriptEnabled):
            return False
        return True

    @classmethod
    def pushView(cls, view):
        '''
        @param: view QWebEngineView
        '''
        cls._s_views.remove(view)
        cls._s_views.insert(0, view)

    @classmethod
    def registerView(cls, view):
        '''
        @param: view QWebEngineView
        '''
        cls._s_views.insert(0, view)

    @classmethod
    def unregisterView(cls, view):
        '''
        @param: view QWebEngineView
        '''
        cls._s_views.remove(view)

    # private Q_SLOTS:
    def _loadFinished(self):
        # Show close button only when docked
        if not self.isWindow():
            self.page().runJavaScript('''
var button = Components.dockController._closeButton;
    button.setVisible(true);
    button.element.onmouseup = function() {
    window.close();
};
''')

        # Inspect element
        if self._inspectElement:
            self._view.triggerPageAction(QWebEnginePage.InspectElement)
            self._inspectElement = False

    # private:
    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        # Stop propagation

    # override
    def keyReleaseEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        # Stop propagation
