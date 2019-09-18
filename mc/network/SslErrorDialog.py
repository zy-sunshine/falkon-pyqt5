from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QStyle
from PyQt5.QtWidgets import QDialogButtonBox

class SslErrorDialog(QDialog):
    # enum Result
    Yes = 0
    No = 1
    OnlyForThisSession = 2
    NoForThisSession = 3
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/network/SslErrorDialog.ui', self)
        self._result = self.No

        self._ui.icon.setPixmap(IconProvider.standardIcon(QStyle.SP_MessageBoxCritical).pixmap(52))
        # Disabled untile there is reliable way to save certificate error
        # self._ui.buttonBox.addButton(_('Only for this session'), QDialogButtonBox.ApplyRole)
        self._ui.buttonBox.button(QDialogButtonBox.No).setFocus()

        self._ui.buttonBox.clicked.connect(self._buttonClicked)

    def setText(self, text):
        '''
        @param: text QString
        '''
        self._ui.text.setText(text)

    def result(self):
        '''
        @return: Result
        '''
        return self._result

    # private Q_SLOTS:
    def _buttonClicked(self, button):
        '''
        @param: button QAbstractButton
        '''
        role = self._ui.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.YesRole:
            self._result = self.Yes
            self.accept()
        elif role == QDialogButtonBox.ApplyRole:
            self._result = self.OnlyForThisSession
            self.accept()
        elif role == QDialogButtonBox.NoRole:
            self._result = self.NoForThisSession
            self.reject()
        else:
            self._result = self.No
            self.reject()
