from PyQt5.Qt import QByteArray

class RestoreData(object):
    def __init__(self):
        self.windows = []
        self.crashedSession = QByteArray()
        self.closedWindows = QByteArray()

    def isValid(self):
        for window in self.windows:
            if not window.isValid():
                return False
        return len(window) > 0

    def clear(self):
        self.windows.clear()
        self.crashedSession.clear()
        self.closedWindows.clear()

class RestoreManager(object):
    def __init__(self, fpath):
        self._recoveryObject = None  # RecoveryJsObject
        self._data = RestoreData()

    def isValid(self):
        pass

    def restoreData(self):
        '''
        @return: RestoreData
        '''
        pass

    def clearRestoreData(self):
        pass

    def recoveryObject(self, page):
        '''
        @param: page WebPage
        @return: QObject
        '''
        pass

    @staticmethod
    def validateFile(cls, fpath):
        pass

    @staticmethod
    def createFromFile(self, fpaht, data):
        '''
        @param: data RestoreData
        '''
        pass

    # private:
    def _createFromFile(self, fpath):
        pass
