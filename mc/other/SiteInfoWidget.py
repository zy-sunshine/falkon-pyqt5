from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.Qt import QPixmap
from mc.navigation.LocationBarPopup import LocationBarPopup
from mc.common.models import HistoryDbModel
from mc.common.globalvars import gVar

class SiteInfoWidget(LocationBarPopup):
    def __init__(self, window, parent=None):
        '''
        @param: window BrowserWindow
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/other/SiteInfoWidget.ui', self)
        self._window = window

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setPopupAlignment(Qt.AlignLeft)

        view = self._window.weView()

        self._ui.titleLabel.setText(_('<b>Site %s</b>') % view.url().host())

        if view.url().scheme() == 'https':
            self._ui.secureLabel.setText(_('Your connection to this site is <b>secured</b>.'))
            self._ui.secureIcon.setPixmap(QPixmap(':/icons/locationbar/safe.png'))
        else:
            self._ui.secureLabel.setText(_('Your connection to this site is <b>unsecured</b>'))
            self._ui.secureIcon.setPixmap(QPixmap(':/icons/locationbar/unsafe.png'))

        scheme = view.url().scheme()
        host = view.url().host()

        count = HistoryDbModel.select().where(
            HistoryDbModel.url.contains('%s://%s' % (scheme, host))
        ).count()
        if count > 3:
            self._ui.historyLabel.setText(_('This is your <b>%s</b> visit of this site.') % count)
            self._ui.historyIcon.setPixmap(QPixmap(':/icons/locationbar/visit3.png'))
        elif count == 0:
            self._ui.historyLabel.setText(_('You have <b>never</b> visited this site before.'))
            self._ui.historyIcon.setPixmap(QPixmap(':/icons/locationbar/visit1.png'))
        else:
            self._ui.historyIcon.setPixmap(QPixmap(':/icons/locationbar/visit2.png'))
            text = ''
            if count == 1:
                text = _('first')
            elif count == 2:
                text = _('second')
            elif count == 3:
                text = _('third')
            self._ui.historyLabel.setText(_('This is your <b>%s</b> visit of this site.') % text)

        self._updateProtocolHandler()

        self._ui.pushButton.clicked.connect(self._window.action('Tools/SiteInfo').trigger)
        self._ui.protocolHandlerButton.clicked.connect(self._protocolHandlerButtonClicked)

    # private:
    def _updateProtocolHandler(self):
        # WebPage
        page = self._window.weView().page()

        scheme = page.registerProtocolHandlerRequestScheme()
        registeredUrl = gVar.app.protocolHandlerManager().protocolHandlers().get(scheme)
        if scheme and registeredUrl != page.registerProtocolHandlerRequestUrl():
            self._ui.protocolHandlerLabel.setText(_('Register as <b>%s</b> links handler') % scheme)
            self._ui.protocolHandlerButton.setText(_('Register'))
        else:
            self._ui.protocolHandlerLabel.hide()
            self._ui.protocolHandlerButton.hide()
            self._ui.protocolHandlerLine.hide()

    def _protocolHandlerButtonClicked(self):
        # WebPage
        page = self._window.weView().page()

        gVar.app.protocolHandlerManager().addProtocolHandler(page.registerProtocolHandlerRequestScheme(),
            page.registerProtocolHandlerRequestUrl())
        self.close()
