from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QDialog
from mc.common import const
from mc.app.Settings import Settings

class JsOptions(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._ui = uic.loadUi('mc/preferences/JsOptions.ui', self)

        if const.QTWEBENGINEWIDGETS_VERSION < const.QT_VERSION_CHECK(5, 10, 0):
            self._ui.jscanActivateWindow.setVisible(False)
        if const.QTWEBENGINEWIDGETS_VERSION < const.QT_VERSION_CHECK(5, 11, 0):
            self._ui.jscanPaste.setVisible(False)

        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        self._ui.jscanOpenWindow.setChecked(settings.value('allowJavaScriptOpenWindow', False))
        self._ui.jscanActivateWindow.setChecked(settings.value('allowJavaScriptActivationWindow', False))
        self._ui.jscanAccessClipboard.setChecked(settings.value('allowJavaScriptAccessClipboard', True))
        self._ui.jscanPaste.setChecked(settings.value('allowJavaScriptPaste', True))
        settings.endGroup()

    # public Q_SLOTS:
    def accept(self):
        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        settings.setValue('allowJavaScriptOpenWindow', self._ui.jscanOpenWindow.isChecked())
        settings.setValue('allowJavaScriptActivationWindow', self._ui.jscanActivateWindow.isChecked())
        settings.setValue('allowJavaScriptAccessClipboard', self._ui.jscanAccessClipboard.isChecked())
        settings.setValue('allowJavaScriptPaste', self._ui.jscanPaste.isChecked())
        settings.endGroup()

        self.close()
