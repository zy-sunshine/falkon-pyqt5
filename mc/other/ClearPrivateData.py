from PyQt5 import uic
from PyQt5.Qt import QDialog
from PyQt5.Qt import pyqtSlot
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QApplication
from PyQt5.Qt import Qt
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QDate
from PyQt5.Qt import QTimer
from PyQt5.Qt import QFileInfo
from PyQt5.QtWidgets import QMessageBox
from mc.app.Settings import Settings
from mc.app.DataPaths import DataPaths
from mc.common.globalvars import gVar
from mc.tools.IconProvider import IconProvider
from mc.cookies.CookieManager import CookieManager

class ClearPrivateData(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/other/ClearPrivateData.ui', self)
        self._ui.buttonBox.setFocus()
        self._ui.history.clicked.connect(self._historyClicked)
        self._ui.clear.clicked.connect(self._dialogAccepted)
        self._ui.optimizeDb.clicked.connect(self._optimizeDb)
        self._ui.editCookies.clicked.connect(self._showCookieManager)

        settings = Settings()
        settings.beginGroup('ClearPrivateData')
        self._restoreState(settings.value('state', QByteArray()))
        settings.endGroup()

    @classmethod
    def clearLocalStorage(cls):
        profile = DataPaths.currentProfilePath()

        gVar.appTools.removeRecursively(profile + '/Local Storage')

    @classmethod
    def clearWebDatabases(cls):
        profile = DataPaths.currentProfilePath()

        gVar.appTools.removeRecursively(profile + '/IndexedDB')
        gVar.appTools.removeRecursively(profile + '/databases')

    @classmethod
    def clearCache(cls):
        profile = DataPaths.currentProfilePath()

        gVar.appTools.removeRecursively(profile + '/GPUCache')

        gVar.app.webProfile().clearHttpCache()

    # private Q_SLOTS:
    @pyqtSlot(bool)
    def _historyClicked(self, state):
        '''
        @param: state bool
        '''
        self._ui.historyLength.setEnabled(state)

    @pyqtSlot()
    def _dialogAccepted(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

        if self._ui.history.isChecked():
            start = QDateTime.currentMSecsSinceEpoch()
            end = 0

            # QDate
            today = QDate.currentDate()
            week = today.addDays(1 - today.dayOfWeek())
            month = QDate(today.year(), today.month(), 1)

            index = self._ui.historyLength.currentIndex()
            if index == 0:  # Later Today
                end = QDateTime(today).toMSecsSinceEpoch()
            elif index == 1:  # Week
                end = QDateTime(week).toMSecsSinceEpoch()
            elif index == 2:  # Month
                end = QDateTime(month).toMSecsSinceEpoch()
            elif index == 3:  # All
                end = 0

            if end == 0:
                gVar.app.history().clearHistory()
            else:
                indexes = gVar.app.history().indexesFromTimeRange(start, end)
                gVar.app.history().deleteHistoryEntry(indexes)

        if self._ui.cookies.isChecked():
            gVar.app.cookieJar().deleteAllCookies()

        if self._ui.cache.isChecked():
            self.clearCache()

        if self._ui.databases.isChecked():
            self.clearWebDatabases()

        if self._ui.localStorage.isChecked():
            self.clearLocalStorage()

        QApplication.restoreOverrideCursor()

        self._ui.clear.setEnabled(False)
        self._ui.clear.setText(_('Done'))

        QTimer.singleShot(1000, self.close)

    @pyqtSlot()
    def _optimizeDb(self):
        gVar.app.setOverrideCursor(Qt.WaitCursor)
        profilePath = DataPaths.currentProfilePath()
        sizeBefore = gVar.appTools.fileSizeToString(QFileInfo(profilePath + 'browserdata.db').size())

        IconProvider.instance().clearOldIconsInDatabase()

        sizeAfter = gVar.appTools.fileSizeToString(QFileInfo(profilePath + 'browserdata.db').size())

        gVar.app.restoreOverrideCursor()

        QMessageBox.information(self, _('Database Optimized'),
            _('Database successfully optimized.<br/><br/><b>Database Size Before: </b>%s<br/><b>Database Size After: </b>%s') %  # noqa E501
            (sizeBefore, sizeAfter))

    @pyqtSlot()
    def _showCookieManager(self):
        dialog = CookieManager(self)
        dialog.show()

    # private:
    # override
    def closeEvent(self, event):
        '''
        @param: event QCloseEvent
        '''
        settings = Settings()
        settings.beginGroup('ClearPrivateData')
        settings.setValue('state', self._saveState())
        settings.endGroup()

        event.accept()

    _s_stateDataVersoin = 0x0001
    def _restoreState(self, state):
        '''
        @param: state QByteArray
        '''
        stream = QDataStream(state)
        if stream.atEnd():
            return

        version = -1
        historyIndex = -1
        databases = False
        localStorage = False
        cache = False
        cookies = False

        version = stream.readInt()
        if version != self._s_stateDataVersoin:
            return

        historyIndex = stream.readInt()
        databases = stream.readBool()
        localStorage = stream.readBool()
        cache = stream.readBool()
        cookies = stream.readBool()

        if historyIndex != -1:
            self._ui.history.setChecked(True)
            self._ui.historyLength.setEnabled(True)
            self._ui.historyLength.setCurrentIndex(historyIndex)

        self._ui.databases.setChecked(databases)
        self._ui.localStorage.setChecked(localStorage)
        self._ui.cache.setChecked(cache)
        self._ui.cookies.setChecked(cookies)

    def _saveState(self):
        '''
        @return: QByteArray
        '''
        # history - web database - local storage - cache - icons
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)

        stream.writeInt(self._s_stateDataVersoin)

        if not self._ui.history.isChecked():
            stream.writeInt(-1)
        else:
            stream.writeInt(self._ui.historyLength.currentIndex())

        stream.writeBool(self._ui.databases.isChecked())
        stream.writeBool(self._ui.localStorage.isChecked())
        stream.writeBool(self._ui.cache.isChecked())
        stream.writeBool(self._ui.cookies.isChecked())

        return data
