from PyQt5.Qt import QByteArray
from PyQt5.QtWebEngineCore import QWebEngineHttpRequest
from PyQt5.Qt import QUrl

class LoadRequest(object):
    # enum Operation
    GetOperation = 0
    PostOperation = 1

    def __init__(self, url=QUrl(), op=GetOperation, data=QByteArray()):
        if not isinstance(url, QUrl):
            url = QUrl(url)
        self._url = url
        self._op = op
        self._data = data

    def isValid(self):
        return self._url.isValid()

    def url(self):
        return self._url

    def setUrl(self, url):
        self._url = url

    def urlString(self):
        '''
        @return: String
        '''
        return QUrl.fromPercentEncoding(self._url.toEncoded())

    def operation(self):
        return self._op

    def setOperation(self, op):
        self._op = op

    def data(self):
        return self._data

    def setData(self, data):
        self._data = data

    def webRequest(self):
        '''
        @return: QWebEngineHttpRequest
        '''
        if self._op == self.GetOperation:
            method = QWebEngineHttpRequest.Get
        else:
            method = QWebEngineHttpRequest.Post
        req = QWebEngineHttpRequest(self._url, method)
        req.setPostData(self._data)
        return req
