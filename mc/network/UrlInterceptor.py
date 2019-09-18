from PyQt5.Qt import QObject

class UrlInterceptor(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def interceptRequest(self, info):
        '''
        @note: Runs on IO Thread!
        @param: info QWebEngineUrlRequestInfo
        '''
        raise NotImplementedError
