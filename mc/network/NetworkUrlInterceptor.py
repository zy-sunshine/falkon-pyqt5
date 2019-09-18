from threading import Lock
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from mc.app.Settings import Settings
from mc.common.globalvars import gVar

class NetworkUrlInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = Lock()
        self._interceptors = []  # QList<UrlInterceptor>
        self._sendDNT = False
        self._usePerDomainUserAgent = False
        self._userAgentsList = {}  # QHash<QString, QString>

    # override
    def interceptRequest(self, info):
        '''
        @param: info QWebEngineUrlRequestInfo
        '''
        with self._mutex:
            if self._sendDNT:
                info.setHttpHeader(b'DNT', b'1')

        host = info.firstPartyUrl().host()

        if self._usePerDomainUserAgent:
            userAgent = ''
            if host in self._userAgentsList:
                userAgent = self._userAgentsList[host]
            else:
                for key, val in self._userAgentsList.items():
                    if host.endswith(key):
                        userAgent = val
                        break
            if userAgent:
                info.setHttpHeader(b'User-Agent', userAgent.encode())

        for interceptor in self._interceptors:
            interceptor.interceptRequest(info)

    def installUrlInterceptor(self, interceptor):
        '''
        @param: interceptor UrlInterceptor
        '''
        with self._mutex:
            if interceptor not in self._interceptors:
                self._interceptors.append(interceptor)

    def removeUrlInterceptor(self, interceptor):
        '''
        @param: interceptor UrlInterceptor
        '''
        with self._mutex:
            if interceptor in self._interceptors:
                self._interceptors.remove(interceptor)

    def loadSettings(self):
        with self._mutex:
            settings = Settings()
            settings.beginGroup('Web-Browser-Settings')
            self._sendDNT = settings.value('DoNotTrack', False)
            settings.endGroup()

            self._usePerDomainUserAgent = gVar.app.userAgentManager().usePerDomainUserAgents()
            self._userAgentsList = gVar.app.userAgentManager().perDomainUserAgentsList()
