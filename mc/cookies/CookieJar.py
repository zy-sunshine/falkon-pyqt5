from PyQt5.Qt import QObject
from PyQt5.Qt import QNetworkCookie
from PyQt5.Qt import pyqtSignal
from mc.common.globalvars import gVar
from mc.app.Settings import Settings

class CookieJar(QObject):
    DEBUG = True
    def __init__(self, parent=None):
        super().__init__(parent)
        self._allowCookies = False
        self._filterTrackingCookie = False
        self._filterThirdParty = False

        self._whitelist = []  # QStringList
        self._blacklist = []  # QStringList

        self._client = None  # QWebEngineCookieStore
        self._cookies = []  # QVector<QNetworkCookie>

        self._client = gVar.app.webProfile().cookieStore()
        self.loadSettings()
        self._client.loadAllCookies()

        self._client.setCookieFilter(self._cookieFilter)

        self._client.cookieAdded.connect(self._slotCookieAdded)
        self._client.cookieRemoved.connect(self._slotCookieRemoved)

    def __del__(self):
        self._client.setCookieFilter(None)

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Cookie-Settings')
        self._allowCookies = settings.value('allowCookies', True)
        self._filterThirdParty = settings.value('filterThirdPartyCookies', False)
        self._filterTrackingCookie = settings.value('filterTrackingCookie', False)
        self._whitelist = settings.value('whitelist', [])
        self._blacklist = settings.value('blacklist', [])
        settings.endGroup()

    def setAllowCookies(self, allow):
        '''
        @param: allow bool
        '''
        self._allowCookies = allow

    def deleteCookie(self, cookie):
        self._client.deleteCoolie(cookie)

    def getAllCookies(self):
        '''
        @return: QVector<QNetworkCookie>
        '''
        return self._cookies

    def deleteAllCookies(self, deleteAll=True):
        if deleteAll or not self._whitelist:
            self._client.deleteAllCookies()
            return

        # QNetworkCookie cookie
        for cookie in self._cookies:
            if not self._listMatchesDomain(self._whitelist, cookie.domain()):
                self._client.delete(cookie)

    # Q_SIGNALS
    cookieAdded = pyqtSignal(QNetworkCookie)  # cookie
    cookieRemoved = pyqtSignal(QNetworkCookie)  # cookie

    # protected:
    def _matchDomain(self, cookieDomain, siteDomain):
        '''
        @note: According to RFC 6265
        @param: cookieDomain QString
        @param: siteDomain QString
        '''
        # Remove leading dot
        cookieDomain = cookieDomain.lstrip('.')
        siteDomain = siteDomain.lstrip('.')

        return gVar.appTools.matchDomain(cookieDomain, siteDomain)

    def _listMatchesDomain(self, list_, cookieDomain):
        '''
        @param: list_ QStringList
        @param: cookieDomain QString
        '''
        for item in list_:
            if self._matchDomain(item, cookieDomain):
                return True

        return False

    # private:
    def _slotCookieAdded(self, cookie):
        '''
        @param: cookie QNetworkCookie
        '''
        if self._rejectCookie('', cookie, cookie.domain()):
            self._client.deleteCookie(cookie)
            return

        self._cookies.append(QNetworkCookie(cookie))
        self.cookieAdded.emit(cookie)

    def _slotCookieRemoved(self, cookie):
        '''
        @param: cookie QNetworkCookie
        '''
        try:
            self._cookies.remove(cookie)
            self.cookieRemoved.emit(cookie)
        except ValueError:
            pass

    def _cookieFilter(self, request):
        '''
        @param: request QWebEngineCookieStore
        '''
        if not self._allowCookies:
            result = self._listMatchesDomain(self._whitelist, request.origin.host())
            if not result:
                self._debug('DEBUG: not in whitelist', request.origin)
                return False
        else:
            result = self._listMatchesDomain(self._blacklist, request.origin.host())
            if result:
                self._debug('DEBUG: found in blacklist', request.origin.host())
                return False

        if self._filterThirdParty and request.thirdParty:
            self._debug('DEBUG: thirdParty', request.firstPartyUrl, request.origin)
            return False

        return True

    def _acceptCookie(self, firstPartyUrl, cookieLine, cookieSource):
        '''
        @param: firstPartyUrl QUrl
        @param: cookieLine QByteArray
        @param: cookieSource QUrl
        '''
        # TODO: not implement in falkon
        pass

    def _rejectCookie(self, domain, cookie, cookieDomain):
        '''
        @param: domain QString
        @param: cookie QNetworkCookie
        @param: cookieDomain QString
        '''
        # UNUSED(domain)
        if not self._allowCookies:
            result = self._listMatchesDomain(self._whitelist, cookieDomain)
            if not result:
                self._debug('DEBUG: not in whitelist', cookie)
                return True
        else:
            result = self._listMatchesDomain(self._blacklist, cookieDomain)
            if result:
                self._debug('DEBUG: found in blacklist', cookie)
                return True

        ## ifdef QTWEBENGINE_DISABLED
        #if self._filterThirdParty:
        #    result = self._matchDomain(cookieDomain, domain)
        #    if not result:
        #        self._debug('purged for domain mismatch', cookie, cookieDomain, domain)
        #        return True
        # endif

        if self._filterTrackingCookie and cookie.name().startswith('__utm'):
            self._debug('DEBUG: purged as tracking', cookie)
            return True

        return False

    def _debug(self, *args):
        if self.DEBUG:
            print(*args)
