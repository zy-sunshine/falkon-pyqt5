from PyQt5.Qt import QObject
from mc.app.Settings import Settings
from PyQt5.Qt import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage

class ProtocolHandlerManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocolHandlers = {}  # QHash<QString, QUrl>

        self._init()

    def protocolHandlers(self):
        '''
        @return: QHash<QString, QUrl>
        '''
        return self._protocolHandlers

    def addProtocolHandler(self, scheme, url):
        '''
        @param: scheme QString
        @param: url QUrl
        '''
        if not scheme or url.isEmpty():
            return
        self._protocolHandlers[scheme] = url
        self._registerHandler(scheme, url)
        self._save()

    def removeProtocolHandler(self, scheme):
        '''
        @param: scheme QString
        '''
        self._protocolHandlers.pop(scheme)
        self._save()

    # private:
    def _init(self):
        settings = Settings()
        settings.beginGroup('ProtocolHandlers')
        keys = settings.childKeys()
        for scheme in keys:
            url = settings.value(scheme, type=QUrl)
            self._protocolHandlers[scheme] = url
            self._registerHandler(scheme, url)
        settings.endGroup()

    def _save(self):
        settings = Settings()
        settings.remove('ProtocolHandlers')
        settings.beginGroup('ProtocalHandlers')
        for key, val in self._protocolHandlers.items():
            settings.setValue(key, val)
        settings.endGroup()

    def _registerHandler(self, scheme, url):
        '''
        @param: scheme QString
        @param: url QUrl
        '''
        urlString = url.toString()
        urlString = urlString.replace('%25s', '%s')

        page = QWebEnginePage(self)
        page.loadFinished.connect(page.deleteLater)
        page.registerProtocolHandlerRequested.connect(lambda request: request.accept())
        page.setHtml('<script>navigator.registerProtocolHandler("%s", "%s", "")</script>' %
                (scheme, urlString), url)
