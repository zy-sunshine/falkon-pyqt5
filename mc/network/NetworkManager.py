from PyQt5.Qt import QNetworkAccessManager
from mc.common.globalvars import gVar
from mc.webengine.WebPage import WebPage
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.Qt import QAuthenticator
from PyQt5.Qt import QNetworkProxy
from PyQt5.Qt import QNetworkProxyFactory
from PyQt5.Qt import QNetworkRequest
from mc.app.Settings import Settings
from .NetworkUrlInterceptor import NetworkUrlInterceptor

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

        # Create url interceptor
        self._urlInterceptor = NetworkUrlInterceptor(self)
        gVar.app.webProfile().setRequestInterceptor(self._urlInterceptor)

        # Create cookie jar
        gVar.app.cookieJar()

        # QNetworkReply reply, QAuthenticator auth
        self.authenticationRequired.connect(lambda reply, auth: self.authentication(reply.url(), auth))
        # QNetworkProxy proxy, QAuthenticator auth
        self.proxyAuthenticationRequired.connect(lambda proxy, auth: self.proxyAuthentication(proxy.hostHame(), auth))

    def certificateError(self, error, parent=None):
        '''
        @param: error QWebEngineCertificateError
        '''
        host = error.url().host()

        if host in self._rejectedSslErrors and self._rejectedSslErrors[host] == error.error():
            return False

        if host in self._ignoredSslErrors and self._ignoredSslErrors[host] == error.error():
            return True

        title = _('SSL Certificate Error')
        text1 = _('The page you are trying to access has the following errors in the SSL certificate:')
        text2 = _('Would you like to make an exception for this certificate?')

        message = "<b>%s</b><p>%s</p><ul><li>%s</li></ul><p>%s</p>" % \
            (title, text1, error.errorDescription(), text2)

        dialog = SslErrorDialog(parent)
        dialog.setText(message)
        dialog.exec_()

        res = dialog.result()
        if res == SslErrorDialog.Yes:
            # TODO: Permanent exceptions
            self._ignoredSslErrors[host] = error.error()
            return True
        elif res == SslErrorDialog.OnlyForThisSession:
            self._ignoredSslErrors[host] = error.error()
            return True
        elif res == SslErrorDialog.NoForThisSession:
            self._rejectedSslErrors[host] = error.error()
            return False
        return False

    def authentication(self, url, auth, parent=None):
        '''
        @param: url QUrl
        @param: auth QAuthenticator
        '''
        dialog = QDialog(parent)
        dialog.setWindowTitle(_('Authorization required'))

        formLa = QFormLayout(dialog)

        label = QLabel(dialog)
        userLab = QLabel(dialog)
        passLab = QLabel(dialog)
        userLab.setText(_('Username: '))
        passLab.setText(_('Password: '))

        user = QLineEdit(dialog)
        pass_ = QLineEdit(dialog)
        pass_.setEchoMode(QLineEdit.Password)
        save = QCheckBox(dialog)
        save.setText(_('Save username and password for this site'))

        box = QDialogButtonBox(dialog)
        box.addButton(QDialogButtonBox.Ok)
        box.addButton(QDialogButtonBox.Cancel)
        box.rejected.connect(dialog.reject)
        box.accepted.connect(dialog.accepted)

        label.setText(_('A username and password are being requested by %s. The site says: "%s"') %
                (url.host(), auth.realm().toHtmlEscaped()))

        formLa.addRow(label)
        formLa.addRow(userLab, user)
        formLa.addRow(passLab, pass_)
        formLa.addRow(save)
        formLa.addWidget(box)

        fill = gVar.app.autoFill()
        storedUser = ''
        storedPassword = ''
        shouldUpdateEntry = False

        if fill.isStored(url):
            data = fill.getFormData(url)
            if data:
                save.setChecked(True)
                shouldUpdateEntry = True
                storedUser = data[0].username
                storedPassword = data[0].password
                user.setText(storedUser)
                pass_.setText(storedPassword)

        # Do not save when private browsing is enabled
        if gVar.app.isPrivate():
            save.setVisible(False)

        if dialog.exec_() != QDialog.Accepted:
            auth = QAuthenticator()
            del dialog
            return auth  # TODO: C++ return, but should assign auth, try return auth in python, to be check

        auth.setUser(user.text())
        auth.setPassword(pass_.text())

        if save.isChecked():
            if shouldUpdateEntry:
                if storedUser != user.text() or storedPassword != pass_.text():
                    fill.updateEntry(url, user.text(), pass_.text())
            else:
                fill.addEntry(url, user.text(), pass_.text())

        del dialog

    def proxyAuthentication(self, proxyHost, auth, parent=None):
        '''
        @param: proxyHost QString
        @param: auth QAuthenticator
        '''
        proxy = QNetworkProxy.applicationProxy()
        if proxy.user() and proxy.password():
            auth.setUser(proxy.user())
            auth.setPassword(proxy.password())
            return

        dialog = QDialog(parent)
        dialog.setWindowTitle(_('Proxy authorization required'))

        formLa = QFormLayout(dialog)

        label = QLabel(dialog)
        userLab = QLabel(dialog)
        passLab = QLabel(dialog)
        userLab.setText(_('Username: '))
        userLab.setText(_('Password: '))

        user = QLineEdit(dialog)
        pass_ = QLineEdit(dialog)
        pass_.setEchoMode(QLineEdit.Password)

        box = QDialogButtonBox(dialog)
        box.addButton(QDialogButtonBox.Ok)
        box.addButton(QDialogButtonBox.Cancel)
        box.rejected.connect(dialog.reject)
        box.accepted.connect(dlalog.accept)

        label.setText(_('A username and password are being requested by proxy %s. ') % proxyHost)
        formLa.addRow(label)
        formLa.addRow(userLab, user)
        formLa.addRow(passLab, pass_)
        formLa.addWidget(box)

        if dialog.exec_() != QDialog.Accepted:
            auth = QAuthenticator
            del dialog
            return auth  # TODO: C++ return, but should assign auth, try return auth in python, to be check

        auth.setUser(user.text())
        auth.setPassword(pass_.text())

        del dialog

    def installUrlInterceptor(self, interceptor):
        '''
        @param: interceptor UrlInterceptor
        '''
        self._urlInterceptor.installUrlInterceptor(interceptor)

    def removeUrlInterceptor(self, interceptor):
        '''
        @param: interceptor UrlInterceptor
        '''
        self._urlInterceptor.removeUrlInterceptor(interceptor)

    def registerExtensionSchemeHandler(self, name, handler):
        '''
        @param: name QString
        @param: handler ExtensionSchemeHandler
        '''
        self._extensionScheme.registerHandler(name, handler)

    def unregisterExtensionSchemeHandler(self, handler):
        '''
        @param: handler ExtensionSchemeHandler
        '''
        self._extensionScheme.unregisterHandler(handler)

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Language')
        # TODO:
        #langs = settings.value('acceptLanguage', AcceptLanguage.defaultLanguage(), type=[])
        settings.endGroup()
        # TODO:
        #gVar.app.webProfile().setHttpAcceptLanguage(AcceptLanguage.generateHeader(langs))

        proxy = QNetworkProxy()
        settings.beginGroup('Web-Proxy')
        proxyType = settings.value('ProxyType', 2)
        proxy.setHostName(settings.value('HostName', ''))
        proxy.setPort(settings.value('Port', 8080))
        proxy.setUser(settings.value('Username', ''))
        proxy.setPassword(settings.value('Password', ''))
        settings.endGroup()

        if proxyType == 0:
            proxy.setType(QNetworkProxy.NoProxy)
        elif proxyType == 3:
            proxy.setType(QNetworkProxy.HttpProxy)
        elif proxyType == 4:
            proxy.setType(QNetworkProxy.Socks5Proxy)

        if proxyType == 2:
            QNetworkProxy.setApplicationProxy(QNetworkProxy())
            QNetworkProxyFactory.setUseSystemConfiguration(True)
        else:
            QNetworkProxy.setApplicationProxy(proxy)
            QNetworkProxyFactory.setUseSystemConfiguration(False)

        self._urlInterceptor.loadSettings()

    def shutdown(self):
        gVar.app.webProfile().setRequestInterceptor(None)

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
        req = QNetworkRequest(request)
        req.setAttribute(QNetworkRequest.SpdyAllowedAttribute, True)
        req.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)

        return QNetworkAccessManager.createRequest(op, req, outgoingData)

