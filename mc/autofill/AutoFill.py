from PyQt5.Qt import QObject
from PyQt5.Qt import QByteArray

class PageFormData:
    def __init__(self):
        self.username = ''
        self.password = ''
        self.postData = QByteArray()

    def isValid(self):
        return bool(self.password)

class AutoFill(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = None  # PasswordManager
        self._isStoring = False
        self._isAutoComplete = False
        self._lastNotification = None  # QPointer<AutoFillNotification>
        self._lastNotificationPage = None  # WebPage

    def passwordManager(self):
        '''
        @return: PasswordManager
        '''
        pass

    def loadSettings(self):
        pass

    def isStored(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def isStoringEnabled(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def blockStoringforUrl(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def getFormData(self, url):
        '''
        @param: url QUrl
        @return: QVector<PasswordEntry>
        '''
        pass

    def getAllFormData(self):
        '''
        @return: QVector<PasswordEntry>
        '''
        pass

    def updateLastUsed(self, data):
        '''
        @param: data PasswordEntry
        '''
        pass

    def addEntryByUrlNamePasswd(self, url, name, passwd):
        '''
        @param: url QUrl
        @param: name QString
        @param: passwd QString
        '''
        pass

    def addEntryByUrlFormData(self, url, formData):
        '''
        @param: url QUrl
        @param: formData PageFormData
        '''
        pass

    def updateEntryByUrlNamePasswd(self, url, name, passwd):
        '''
        @param: url QUrl
        @param: name QString
        @param: passwd QString
        '''
        pass

    def updateEntryByEntry(self, entry):
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

    def saveForm(self, page, frameUrl, formData):
        '''
        @param: page WebPage
        @param: frameUrl QUrl
        @param: formData PageFormData
        '''
        pass

    def completePage(self, page, frameUrl):
        '''
        @param: page WebPage
        @param: frameUrl QUrl
        @return: QStringList
        '''
        pass

    def exportPasswords(self):
        '''
        @return: QByteArray
        '''
        pass

    def importPasswords(self, data):
        '''
        @param: data QByteArray
        '''
        pass
