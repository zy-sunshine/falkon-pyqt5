from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal

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
        self._sessionMetaDataList = []  # QList<SessionMetaData>

        self._firstBackupSession = ''
        self._secondBackupSession = ''
        self._lastActiveSessionPath = ''

    def loadSettings(self):
        pass

    def saveSettings(self):
        pass

    @staticmethod
    def defaultSessionPath(cls):
        '''
        @return: QString
        '''
        pass

    def lastActiveSessionPath(self):
        '''
        @return: QString
        '''
        pass

    def askSessionFromUser(self):
        '''
        @return: QString
        '''
        pass

    def backupSavedSessions(self):
        pass

    def writeCurrentSession(self, filePath):
        pass

    # Q_SIGNALS:
    sessionsMetaDataChanged = pyqtSignal()

    # public Q_SLOTS:
    def autoSaveLastSession(self):
        pass

    def openSessionManagerDialog(self):
        pass

    # private Q_SLOTS:
    def _aboutToShowSessionsMenu(self):
        pass

    def _sessionsDirectoryChanged(self):
        pass

    def _openSession(self, sessionFilePath='', flags=0):
        pass

    def _renameSession(self, sessionFilePath='', flags=0):
        pass

    def _saveSession(self):
        pass

    def _replaceSession(self, filePath):
        pass

    def _switchToSession(self, filePath):
        pass

    def _cloneSession(self, filePath):
        pass

    def _deleteSession(self, filePath):
        pass

    def _newSession(self):
        pass

    def _sessionMetaData(self, withBackups=True):
        '''
        @return: QList<SessionMetaData>
        '''
        pass

    # private:
    def _isActiveFilePath(self, filePath):
        pass

    def _isActiveFileInfo(self, fileInfo):
        pass

    def _fillSessionsMetaDataListIfNeeded(self):
        pass
