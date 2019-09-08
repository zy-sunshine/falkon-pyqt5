from PyQt5.Qt import QNetworkAccessManager
from mc.common.globalvars import gVar
from mc.webengine.WebPage import WebPage

# NOTE: process later
# https://github.com/qutebrowser/qutebrowser/blob/master/qutebrowser/browser/webengine/webenginequtescheme.py
try:
    from PyQt5.QtWebEngineCore import QWebEngineUrlScheme  # type: ignore
except ImportError:
    # Added in Qt 5.12
    QWebEngineUrlScheme = None

from .schemehandlers.AppSchemeHandler import AppSchemeHandler
from .schemehandlers.ExtensionSchemeHandler import ExtensionSchemeManager

class NetworkManager(QNetworkAccessManager):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._urlInterceptor = None  # NetworkUrlInterceptor
        self._extensionScheme = None  # ExtensionSchemeManager
        self._ignoredSslErrors = {}  # QHash<QString, QWebEngineCertificateError::Error>
        self._rejectedSslErrors = {}  # QHash<QString, QWebEngineCertificateError::Error>

        gVar.app.webProfile().installUrlSchemeHandler(b'app',
                AppSchemeHandler())
        self._extensionScheme = ExtensionSchemeManager()
        gVar.app.webProfile().installUrlSchemeHandler(b'extension',
                self._extensionScheme)
        WebPage.addSupportedScheme('app')
        WebPage.addSupportedScheme('extension')

    def certificateError(self, error, parent=None):
        '''
        @param: error QWebEngineCertificateError
        '''
        pass

    def authentication(self, url, auth, parent=None):
        '''
        @param: url QUrl
        @param: auth QAuthenticator
        '''
        pass

    def proxyAuthentication(self, proxyHost, auth, parent=None):
        '''
        @param: proxyHost QString
        @param: auth QAuthenticator
        '''
        pass

    def installUrlInterceptor(self, interceptor):
        '''
        @param: interceptor UrlInterceptor
        '''
        pass

    def removeUrlInterceptor(self, interceptor):
        '''
        @param: interceptor UrlInterceptor
        '''
        pass

    def registerExtensionSchemeHandler(self, name, handler):
        '''
        @param: name QString
        @param: handler ExtensionSchemeHandler
        '''
        pass

    def unregisterExtensionSchemeHandler(self, handler):
        '''
        @param: handler ExtensionSchemeHandler
        '''

    def loadSettings(self):
        pass

    def shutdown(self):
        pass

    @classmethod
    def registerSchemes(cls):
        if QWebEngineUrlScheme:
            appSchema = QWebEngineUrlScheme(b'app')
            appSchema.setFlags(QWebEngineUrlScheme.SecureScheme |
                QWebEngineUrlScheme.ContentSecurityPolicyIgnored)
            appSchema.setSyntax(QWebEngineUrlScheme.Syntax.Path)
            QWebEngineUrlScheme.registerScheme(appSchema)
            extensionScheme = QWebEngineUrlScheme(b'extension')
            extensionScheme.setFlags(QWebEngineUrlScheme.SecureScheme |
                QWebEngineUrlScheme.ContentSecurityPolicyIgnored)
            extensionScheme.setSyntax(QWebEngineUrlScheme.Syntax.Path)
            QWebEngineUrlScheme.registerScheme(extensionScheme)

    # protected:
    # override
    def createRequest(self, op, request, outgoingData):
        '''
        @param: op Operation
        @param: request QNetworkRequest
        @param: outgoingData QIODevice
        @return: QNetworkReply
        '''
        pass
