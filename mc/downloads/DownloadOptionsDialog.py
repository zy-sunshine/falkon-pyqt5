from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import pyqtSignal
from PyQt5 import uic
from PyQt5.Qt import QStyle
from PyQt5.Qt import QIcon
from PyQt5.Qt import QMimeDatabase
from PyQt5.Qt import QApplication
from mc.tools.IconProvider import IconProvider

class DownloadOptionsDialog(QDialog):
    def __init__(self, fileName, downloadItem, parent=None):
        '''
        @param: fileName QString
        @param: downloadItem QWebEngineDownloadItem
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/downloads/DownloadOptionsDialog.ui', self)
        self._downloadItem = downloadItem
        self._signalEmited = False

        self._ui.fileName.setText('<b>%s</b>' % fileName)
        self._ui.fromServer.setText(self._downloadItem.url().host())

        fileIcon = IconProvider.standardIcon(QStyle.SP_FileIcon)

        db = QMimeDatabase()
        # QMimeType
        mime = db.mimeTypeForName(downloadItem.mimeType())
        if mime.isValid() and not mime.isDefault():
            self._ui.mimeName.setText(mime.comment())
            self._ui.iconLabel.setPixmap(QIcon.fromTheme(mime.iconName(), fileIcon).pixmap(22))
        else:
            self._ui.mimeFrame.hide()
            self.iconLabel.setPixmap(fileIcon.pixmap(22))

        self.setWindowTitle(_('Opening %s') % fileName)

        self._ui.buttonBox.setFocus()

        self._ui.copyDownloadLink.clicked.connect(self._copyDownloadLink)
        self._ui.finished.connect(self._emitDialogFinished)

    def showExternalManagerOption(self, show):
        self._ui.radioExternal.setVisible(show)

    def showFromLine(self, show):
        self._ui.fromFrame.setVisible(show)

    def setLastDownloadOption(self, option):
        '''
        @param: option DownloadManager.DownloadOption
        '''
        from .DownloadManager import DownloadManager
        if option == DownloadManager.ExternalManager:
            if not self._ui.radioExternal.isHidden():
                self._ui.radioExternal.setChecked(True)
            self._ui.raidoOpen.setChecked(True)
        elif option == DownloadManager.OpenFile:
            self._ui.radioOpen.setChecked(True)
        elif option == DownloadManager.SaveFile:
            self._ui.radioSave.setChecked(True)

    # override
    def exec_(self):
        status = super().exec_()

        if status != 0:
            if self._ui.radioOpen.isChecked():
                status = 1
            elif self._ui.radioSave.isChecked():
                status = 2
            elif self._ui.radioExternal.isChecked():
                status = 3

        return status

    # private Q_SLOTS:
    def _copyDownloadLink(self):
        QApplication.clipboard().setText(self._downloadItem.url().toString())
        self._ui.copyDownloadLink.setText(_('Download link copied.'))

    def _emitDialogFinished(self, status):
        if status != 0:
            if self._ui.radioOpen.isChecked():
                status = 1
            elif self._ui.radioSave.isChecked():
                status = 2
            elif self._ui.radioExternal.isChecked():
                status = 3

        self._signalEmited = True
        self.dialogFinished.emit(status)

    # Q_SIGNALS
    dialogFinished = pyqtSignal(int)
