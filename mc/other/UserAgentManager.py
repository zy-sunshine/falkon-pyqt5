import re
from PyQt5.Qt import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from mc.common import const
from mc.app.Settings import Settings

class UserAgentManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._globalUserAgent = ''
        self._defaultUserAgent = ''

        self._usePerDomainUserAgent = False
        self._userAgentsList = {}  # QHash<QString, QString>

        self._defaultUserAgent = QWebEngineProfile.defaultProfile().httpUserAgent()
        self._defaultUserAgent = re.sub(r'QtWebEngine/[^\s]+', 'App/%s' % const.VERSION, self._defaultUserAgent)

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        self._globalUserAgent = settings.value('UserAgent', '', type=str)
        settings.endGroup()

        settings.beginGroup('User-Agent-Settings')
        self._usePerDomainUserAgent = settings.value('UsePerDomainUA', False, type=bool)
        domainList = settings.value('DomainList', [], type=list)
        userAgentsList = settings.value('UserAgentsList', [], type=list)
        settings.endGroup()

        self._usePerDomainUserAgent = self._usePerDomainUserAgent and domainList.count() == userAgentsList.count()

        if self._usePerDomainUserAgent:
            for idx in range(domainList.count()):
                self._userAgentsList[domainList[idx]] = userAgentsList[idx]

        if not self._globalUserAgent:
            userAgent = self._defaultUserAgent
        else:
            userAgent = self._globalUserAgent

        QWebEngineProfile.defaultProfile().setHttpUserAgent(userAgent)

    def globalUserAgent(self):
        return self._globalUserAgent

    def defaultUserAgent(self):
        return self._defaultUserAgent

    def usePerDomainUserAgents(self):
        '''
        @return: bool
        '''
        return self._usePerDomainUserAgent

    def perDomainUserAgentsList(self):
        '''
        @return: QHash<QString, QString>
        '''
        return self._userAgentsList
