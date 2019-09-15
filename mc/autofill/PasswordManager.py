from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QByteArray

class PasswordEntry:
    def __init__(self):
        self.id = None
        self.host = ''
        self.username = ''
        self.password = ''
        self.data = QByteArray()
        self.updated = -1

    def isValid(self):
        return bool(self.password) and bool(self.host)

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.updated > other.updated

class PasswordManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._backend = None  # PasswordBackend
        self._databaseBackend = None  # DatabasePasswordBackend
        self._databaseEncryptedBackend = None  # DatabaseEncryptedPasswordBackend

        self._backends = {}  # QHash<QString, PasswordBackend>

    # Q_SIGNALS:
    _passwordBackendChanged = pyqtSignal()

    def loadSettings(self):
        pass

    def getUsernames(self, url):
        '''
        @param: url QUrl
        @return: QStringList
        '''
        pass

    def getEntries(self, url):
        '''
        @param: url QUrl
        @return: QVector<PasswordEntry>
        '''
        pass

    def getAllEntries(self, url):
        '''
        @param: url QUrl
        @return: QVector<PasswordEntry>
        '''
        pass

    def addEntry(self, entry):
        '''
        @param: entry PasswordEntry
        '''
        pass

    def updateEntry(self, entry):
        '''
        @param: entry PasswordEntry
        '''
        pass

    def updateLastUsed(self, entry):
        '''
        @param: entry PasswordEntry
        '''
        pass

    def removeEntry(self, entry):
        '''
        @param: entry PasswordEntry
        '''
        pass

    def removeAllEntries(self):
        pass

    def availableBackends(self):
        '''
        @return: QHash<QString, PasswordBackend>
        '''
        pass

    def activeBackend(self):
        '''
        @return: PasswordBackend
        '''
        pass

    def swtichBackend(self, backendID):
        '''
        @param: backendID QString
        '''
        pass

    def registerBackend(self, id_, backend):
        '''
        @param: id_ QString
        @param: backend PasswordBackend
        '''
        pass

    def unregisterBackend(self, backend):
        '''
        @param: backend PasswordBackend
        '''
        pass

    @classmethod
    def createHost(cls, url):
        '''
        @param: url QUrl
        @return: QString
        '''
        pass

    @classmethod
    def urlEncodePassword(cls, password):
        '''
        @param: password QString
        @return: QByteArray
        '''
        pass

    # private:
    def _ensureLoaded(self):
        pass
