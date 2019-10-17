from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QFileSystemWatcher
from PyQt5.Qt import QDir
from PyQt5.Qt import QFile
from PyQt5.Qt import QSaveFile
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QActionGroup
from PyQt5.Qt import QAction
from PyQt5.Qt import QFileInfo
from PyQt5.Qt import QDateTime
from PyQt5.Qt import Qt
from PyQt5.Qt import QVBoxLayout
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from mc.app.DataPaths import DataPaths
from mc.common.globalvars import gVar
from mc.app.Settings import Settings
from mc.common import const
from .SessionManagerDialog import SessionManagerDialog
from .RestoreManager import RestoreManager
from .RestoreManager import RestoreData

class SessionManager(QObject):
    class SessionMetaData:
        def __init__(self):
            self.name = ''
            self.filePath = ''
            self.isActive = False
            self.isDefault = False
            self.isBackup = False

    # SessionFlag
    SwitchSession = 1
    CloneSession = 2
    ReplaceSession = SwitchSession | 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessionsMetaDataList = []  # QList<SessionMetaData>

        self._firstBackupSession = DataPaths.currentProfilePath() + '/session.dat.old'
        self._secondBackupSession = DataPaths.currentProfilePath() + '/session.dat.old1'
        self._lastActiveSessionPath = ''

        sessionFileWatcher = QFileSystemWatcher([DataPaths.path(DataPaths.Sessions)], self)
        sessionFileWatcher.directoryChanged.connect(self._sessionsDirectoryChanged)
        sessionFileWatcher.directoryChanged.connect(self.sessionsMetaDataChanged)

        self.loadSettings()

    def loadSettings(self):
        sessionDir = QDir(DataPaths.path(DataPaths.Sessions))

        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        self._lastActiveSessionPath = settings.value('lastActiveSessionPath', self.defaultSessionPath())
        settings.endGroup()

        if QDir.isRelativePath(self._lastActiveSessionPath):
            self._lastActiveSessionPath = sessionDir.absoluteFilePath(self._lastActiveSessionPath)

        # Fallback to default session
        if not RestoreManager.validateFile(self._lastActiveSessionPath):
            self._lastActiveSessionPath = self.defaultSessionPath()

    def saveSettings(self):
        sessionDir = QDir(DataPaths.path(DataPaths.Sessions))

        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        settings.setValue('lastActiveSessionPath', sessionDir.relativeFilePath(self._lastActiveSessionPath))
        settings.endGroup()

    @classmethod
    def defaultSessionPath(cls):
        '''
        @return: QString
        '''
        return DataPaths.currentProfilePath() + '/session.dat'

    def lastActiveSessionPath(self):
        '''
        @return: QString
        '''
        return self._lastActiveSessionPath

    def askSessionFromUser(self):
        '''
        @return: QString
        '''
        self._fillSessionsMetaDataListIfNeeded()

        dialog = QDialog(gVar.app.getWindow(), Qt.WindowStaysOnTopHint)
        label = QLabel(_('Please select the startup session:'), dialog)
        comboBox = QComboBox(dialog)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(comboBox)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)

        lastActiveSessionFileInfo = QFileInfo(self._lastActiveSessionPath)

        for metaData in self._sessionsMetaDataList:
            if QFileInfo(metaData.filePath) != lastActiveSessionFileInfo:
                comboBox.addItem(metaData.name, metaData.filePath)
            else:
                comboBox.insertItem(0, _('%s (last session)') % metaData.name, metaData.filePath)

        comboBox.setCurrentIndex(0)

        if dialog.exec_() == QDialog.Accepted:
            self._lastActiveSessionPath = comboBox.currentData()

        return self._lastActiveSessionPath

    def backupSavedSessions(self):
        if not QFile.exists(self._lastActiveSessionPath):
            return

        if QFile.exists(self._firstBackupSession):
            QFile.remove(self._secondBackupSession)
            QFile.copy(self._firstBackupSession, self._secondBackupSession)

        QFile.remove(self._firstBackupSession)
        QFile.copy(self._lastActiveSessionPath, self._firstBackupSession)

    def writeCurrentSession(self, filePath):
        file_ = QSaveFile(filePath)
        if not file_.open(QIODevice.WriteOnly) or file_.write(gVar.app.saveState()) == -1:
            print('WARNING: Error! can not write the current session file.', filePath, file_.errorString())
            return
        file_.commit()

    # Q_SIGNALS:
    sessionsMetaDataChanged = pyqtSignal()

    # public Q_SLOTS:
    def autoSaveLastSession(self):
        if gVar.app.isPrivate() or gVar.app.windowCount() == 0:
            return

        self.saveSettings()
        self.writeCurrentSession(self._lastActiveSessionPath)

    def openSessionManagerDialog(self):
        dialog = SessionManagerDialog(gVar.app.getWindow())
        dialog.open()

    # private Q_SLOTS:
    def _aboutToShowSessionsMenu(self):
        menu = self.sender()
        menu.clear()

        # QActionGroup
        group = QActionGroup(menu)

        sessions = self._sessionMetaData(False) # withBackups
        # SessionManager::SessionMetaData
        for metaData in sessions:
            action = menu.addAction(metaData.name)
            action.setCheckable(True)
            action.setChecked(metaData.isActive)
            group.addAction(action)

            def func():
                self._switchToSession(metaData.filePath)
            action.triggerd.connect(func)

    def _sessionsDirectoryChanged(self):
        self._sessionsMetaDataList.clear()

    def _openSession(self, sessionFilePath='', flags=0):
        if not sessionFilePath:
            action = self.sender()
            if not isinstance(action, QAction):
                return

            sessionFilePath = action.data()

        if self._isActive(sessionFilePath):
            return

        sessionData = RestoreData()
        RestoreManager.createFromFile(sessionFilePath, sessionData)

        if not sessionData.isValid():
            return

        # BrowserWindow
        window = gVar.app.getWindow()
        if flags & self.SwitchSession:
            self.writeCurrentSession(self._lastActiveSessionPath)

            gVar.app.createWindow(const.BW_OtherRestoredWindow)
            for win in gVar.app.windows():
                if win != window:
                    win.close()

            if not (flags & self.ReplaceSession):
                self._lastActiveSessionPath = QFileInfo(sessionFilePath).canonicalFilePath()
                self._sessionsMetaDataList.clear()

        gVar.app.openSession(window, sessionData)

    def _renameSession(self, sessionFilePath='', flags=0):
        if not sessionFilePath:
            action = self.sender()
            if not isinstance(action, QAction):
                return

            sessionFilePath = action.data()

        suggestedName = QFileInfo(sessionFilePath).completeBaseName() + \
            (flags & self._cloneSession) and _('_cloned') or _('_renamed')

        newName, ok = QInputDialog.getText(gVar.app.activeWindow(),
            (flags & self.CloneSession) and _('Clone Session') or _('Rename Session'),
            _('Please enter a new name:'), QLineEdit.Normal, suggestedName)

        if not ok:
            return

        newSessionPath = '%s/%s.dat' % (DataPaths.path(DataPaths.Sessions), newName)
        if QFile.exists(newSessionPath):
            QMessageBox.information(gVar.app.activeWindow(), _('Error!'),
                    _('The session file "%s" exists. Please enter another name.') % newName)
            self._renameSession(sessionFilePath, flags)
            return

        if flags & self.CloneSession:
            if not QFile.copy(sessionFilePath, newSessionPath):
                QMessageBox.information(gVar.app.activeWindow(), _('Error!'),
                    _('An error occurred when cloning session file.'))
                return
        else:
            if not QFile.rename(sessionFilePath, newSessionPath):
                QMessageBox.information(gVar.app.activeWindow(), _('Error!'),
                    _('An error occurred when renaming session file.'))
                return
            if not self._isActive(sessionFilePath):
                self._lastActiveSessionPath = newSessionPath
                self._sessionsMetaDataList.clear()

    def _saveSession(self):
        sessionName, ok = QInputDialog.getText(gVar.app.getWindow(), _('Save Session'),
            _('Please enter a name to save session:'), QLineEdit.Normal,
            _('Saved Session (%s)') % QDateTime.currentDateTime().toString('yyyy MM dd HH-mm-ss'))

        if not ok:
            return

        filePath = '%s/%s.dat' % (DataPaths.path(DataPaths.Sessions), sessionName)
        if QFile.exists(filePath):
            QMessageBox.information(gVar.app.activeWindow(), _('Error!'),
                _('The session file "%s" exists. Please enter another name.') % sessionName)
            self._saveSession()
            return

        self.writeCurrentSession(filePath)

    def _replaceSession(self, filePath):
        result = QMessageBox.information(gVar.app.activeWindow(), _('Restore Backup'),
            _('Are you sure you want to replace current session?'), QMessageBox.Yes | QMessageBox.No)

        if result == QMessageBox.Yes:
            self._openSession(filePath, self.ReplaceSession)

    def _switchToSession(self, filePath):
        self._openSession(filePath, self.SwitchSession)

    def _cloneSession(self, filePath):
        self._openSession(filePath, self.CloneSession)

    def _deleteSession(self, filePath):
        result = QMessageBox.information(gVar.app.activeWindow(), _('Delete Session'),
            _('Are you sure you want to delete session \'%s\'?') % QFileInfo(filePath).completeBaseName(),
            QMessageBox.Yes | QMessageBox.No)

        if result == QMessageBox.Yes:
            QFile.remove(filePath)

    def _newSession(self):
        sessionName, ok = QInputDialog.getText(gVar.app.getWindow(), _('New Session'),
            _('Please enter a name to create new session:'), QLineEdit.Normal,
            _('New Session (%s)') % QDateTime.currentDateTime().toString('yyyy MM dd HH-mm-ss'))

        if not ok:
            return

        filePath = '%s/%s.dat' % (DataPaths.path(DataPaths.Sessions), sessionName)
        if QFile.exists(filePath):
            QMessageBox.information(gVar.app.activeWindow(), _('Error!'),
                _('The session file "%1" exists. Please enter another name.') % sessionName)
            self._newSession()
            return

        self.writeCurrentSession(self._lastActiveSessionPath)

        window = gVar.app.createWindow(const.BW_NewWindow)
        for win in gVar.app.windows():
            if win != window:
                win.close()

        self._lastActiveSessionPath = filePath
        self.autoSaveLastSession()

    def _sessionMetaData(self, withBackups=True):
        '''
        @return: QList<SessionMetaData>
        '''
        self._fillSessionsMetaDataListIfNeeded()

        out = self._sessionsMetaDataList

        if withBackups and QFile.exists(self._firstBackupSession):
            data = self.SessionMetaData()
            data.name = _('Backup 1')
            data.filePath = self._firstBackupSession
            data.isBackup = True
            out.append(data)
        if withBackups and QFile.exists(self._secondBackupSession):
            data = self.SessionMetaData()
            data.name = _('Backup 2')
            data.filePath = self._secondBackupSession
            data.isBackup = True
            out.append(data)

        return out

    # private:
    def _isActive(self, filePathOrFileInfo):
        '''
        @param: filePath QString
        @param: fileInfo QFileInfo
        '''
        if isinstance(filePathOrFileInfo, QFileInfo):
            fileInfo = filePathOrFileInfo
        else:
            # must be QString
            fileInfo = QFileInfo(filePathOrFileInfo)
        return fileInfo == QFileInfo(self._lastActiveSessionPath)

    def _fillSessionsMetaDataListIfNeeded(self):
        if self._sessionsMetaDataList:
            return

        dir_ = QDir(DataPaths.path(DataPaths.Sessions))

        sessionFiles = []
        sessionFiles.append(QFileInfo(self.defaultSessionPath()))
        sessionFiles.extend(dir_.entryInfoList(['*.*'], QDir.Files, QDir.Time))

        fileNames = []

        defaultFileInfo = QFileInfo(self.defaultSessionPath())
        for fileInfo in sessionFiles:
            if not RestoreManager.validateFile(fileInfo.absoluteFilePath()):
                continue

            metaData = self.SessionMetaData()
            metaData.name = baseName = fileInfo.completeBaseName()

            if fileInfo == defaultFileInfo:
                metaData.name = _('Default session')
                metaData.isDefault = True
            elif baseName in fileNames:
                metaData.name = fileInfo.fileName()

            if self._isActive(fileInfo):
                metaData.isActive = True

            fileNames.append(metaData.name)
            metaData.filePath = fileInfo.canonicalFilePath()

            self._sessionsMetaDataList.append(metaData)
