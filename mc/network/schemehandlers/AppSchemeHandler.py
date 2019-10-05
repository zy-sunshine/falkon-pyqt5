from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestJob
from PyQt5.Qt import QIODevice
from threading import Lock
from PyQt5.Qt import QUrlQuery, QUrl
from mc.common import const
from mc.common.globalvars import gVar
from io import BytesIO

class AppSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent=None):
        super().__init__(parent)

    # reload
    # override
    def requestStarted(self, job):
        '''
        @param: job QWebEngineUrlRequestJob
        '''
        if self._handleRequest(job):
            return

        knownPages = ['about', 'start', 'speeddial', 'config', 'restore']

        if job.requestUrl().path() in knownPages:
            job.reply(b'text/html', AppSchemeReply(job, job))
        else:
            job.fail(QWebEngineUrlRequestJob.UrlInvalid)

    # private:
    def _handleRequest(self, job):
        '''
        @param: job QWebEngineUrlRequestJob
        '''
        reqUrl = job.requestUrl()
        query = QUrlQuery(reqUrl)
        if not query.isEmpty() and reqUrl.path() == 'restore':
            if gVar.app.restoreManager():
                if query.hasQueryItem('new-session'):
                    gVar.app.restoreManager().clearRestoreData()
                elif query.hasQueryItem('restore-session'):
                    gVar.app.restoreSession(None, gVar.app.restoreManager().restoreData())
            gVar.app.destroyRestoreManager()
            job.redirect('app:start')
            return True
        elif reqUrl.path() == 'reportbug':
            job.redirect(QUrl(const.BUGSADDRESS))
            return True
        return False

class AppSchemeReply(QIODevice):
    def __init__(self, job, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._buffer = BytesIO()  # QBuffer
        self._pageName = ''
        self._job = job  # QWebEngineUrlRequestJob
        self._mutex = Lock()  # QMutex

        self._pageName = self._job.requestUrl().path()
        self._loadPage()

    # override
    def bytesAvailable(self):
        '''
        @return: qint64
        '''
        with self._mutex:
            return len(self._buffer.getbuffer()) - self._buffer.tell()

    # override
    def readData(self, maxSize):
        '''
        @return: char* data, qint64 maxSize
        '''
        with self._mutex:
            return self._buffer.read(maxSize)

    # override
    def writeData(self, data, len_):
        '''
        @param: data const char*
        @param: len_ qint64
        '''
        return 0

    # private Q_SLOTS:
    def _loadPage(self):
        if self._loaded: return

        contents = ''

        tpl = '<html><head></head><title>%(title)s</title><body><p>%(content)s</p></body></html>'
        if self._pageName == 'about':
            contents = tpl % {'title': 'about', 'content': 'About Page'}
        elif self._pageName == 'start':
            contents = tpl % {'title': 'start', 'content': 'Start Page'}
        elif self._pageName == 'speeddial':
            contents = tpl % {'title': 'speeddial', 'content': 'Speeddial Page'}
        elif self._pageName == 'config':
            contents = tpl % {'title': 'config', 'content': 'Config Page'}
        elif self._pageName == 'restore':
            contents = tpl % {'title': 'restore', 'content': '''Restore Page<br/>
                <a onclick="javascript: alert('test')">alert</a><br/>
                <a onclick="javascript: confirm('confirm test')">confirm</a><br/>
                <a onclick="javascript: prompt('prompt test', 'prompt content')">prompt</a><br/>
                <input type="file" name="myFile" accept="image/x-png" /><br/>
                <a href="mailto:test@test.com"/>mailto</a><br/>
                <a href="appxx:testxx"/>appxx protocol</a>
            '''}

        with self._mutex:
            self._buffer = BytesIO(contents.encode('utf8'))
        self.readyRead.emit()
        self._loaded = True

    # private:
    def _aboutPage(self):
        pass

    def _startPage(self):
        pass

    def _speeddialPage(self):
        pass

    def _restorePage(self):
        pass

    def _configPage(self):
        pass
