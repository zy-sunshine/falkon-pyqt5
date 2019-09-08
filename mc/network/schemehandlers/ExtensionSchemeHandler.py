from PyQt5.Qt import QObject
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from PyQt5.Qt import QBuffer
from PyQt5.Qt import QIODevice
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestJob

class ExtensionSchemeHandler(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def requestStarted(self, job):
        '''
        @param: job QWebEngineUrlRequestJob
        '''
        raise NotImplementedError

    # protected:
    def _setReply(self, job, contentType, content):
        '''
        @param: job QWebEngineUrlRequestJob
        @param: contentType QByteArray
        @param: content QByteArray
        '''
        buf = QBuffer(job)
        buf.open(QIODevice.ReadWrite)
        buf.write(content)
        buf.seek(0)
        job.reply(contentType, buf)

class ExtensionSchemeManager(QWebEngineUrlSchemeHandler):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._handlers = {}  # QHash<QString, ExtensionSchemeHandler>

    # override
    def requestStarted(self, job):
        '''
        @param: job QWebEngineUrlRequestJob
        '''
        handler = self._handlers.get(job.requestUrl().host())
        if handler:
            handler.requestStarted(job)
        else:
            job.fail(QWebEngineUrlRequestJob.UrlInvalid)

    def registerHandler(self, name, handler):
        '''
        @param: name QString
        @param: handler ExtensionSchemeHandler
        '''
        self._handlers[name] = handler

    def unregisterHandler(self, handler):
        '''
        @param: handler ExtensionSchemeHandler
        '''
        key = None
        for key, val in self._handlers.items():
            if val == handler:
                key = key
                break
        if key:
            self._handlers.pop(key, None)
