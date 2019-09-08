from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QCheckBox
from PyQt5.Qt import Qt

class CheckBoxDialog(QMessageBox):
    def __init__(self, buttons, parent=None):
        '''
        @param: buttons QMessageBox.StandardButtons
        '''
        super().__init__(parent)
        self._checkBox = QCheckBox()
        self.setStandardButtons(buttons)
        self.setWindowFlags(self.windowFlags() | Qt.MSWindowsFixedSizeDialogHint |
                Qt.WindowTitleHint | Qt.WindowSystemMenuHint |
                Qt.WindowCloseButtonHint)

    def setCheckBoxText(self, text):
        self._checkBox.setText(text)

    def isChecked(self):
        return self._checkBox.isChecked()

    def setDefaultCheckState(self, state):
        '''
        @param: state Qt.CheckState
        '''
        self._checkBox.setChecked(state == Qt.Checked)
