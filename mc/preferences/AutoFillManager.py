from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from mc.autofill.PasswordManager import PasswordManager

class AutoFillManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/preferences/AutoFillManager.ui', self)

        self._passwordManager = PasswordManager()
        self._fileName = ''
        self._passwordsShown = False

    def showException(self):
        pass

    # private Q_SLOTS:
    def _loadPasswords(self):
        pass

    def _changePasswordBackend(self):
        pass

    def _showBackendOptions(self):
        pass

    def _removePass(self):
        pass

    def _removeAllPass(self):
        pass

    def _editPass(self):
        pass

    def _showPasswords(self):
        pass

    def _copyPassword(self):
        pass

    def _copyUsername(self):
        pass

    def _removeExcept(self):
        pass

    def _removeAllExcept(self):
        pass

    def _importPasswords(self):
        pass

    def _exportPasswords(self):
        pass

    def _slotImportPasswords(self):
        pass

    def _slotExportPasswords(self):
        pass

    def _currentPasswordBackendChanged(self):
        pass

    def _passwordContextMenu(self, pos):
        '''
        @param: pos QPoint
        '''
        pass
