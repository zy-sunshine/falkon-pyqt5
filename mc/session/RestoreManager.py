import pickle
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QFile
from mc.common import const
from .RecoveryJsObject import RecoveryJsObject

class RestoreData(object):
    _s_restoreDataVersion = 2

    def __init__(self):
        self.windows = []  # BrowserWindow.SavedWindow
        self.crashedSession = QByteArray()
        self.closedWindows = QByteArray()

    def isValid(self):
        for window in self.windows:
            if not window.isValid():
                return False
        return len(self.windows) > 0

    def clear(self):
        self.windows.clear()
        self.crashedSession.clear()
        self.closedWindows.clear()

    def __getstate__(self):
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream.writeQVariant(self.windows)

        stream.writeInt(self._s_restoreDataVersion)
        stream.writeQVariant(self.crashedSession)
        stream.writeQVariant(self.closedWindows)

        return data

    def __setstate__(self, state):
        stream = QDataStream(state)
        self.windows = stream.readQVariant()
        assert(type(self.windows) == list)

        version = stream.readInt()
        if version >= 1:
            self.crashedSession = stream.readQVariant()
        if version >= 2:
            self.closedWindows = stream.readQVariant()

class RestoreManager(object):
    def __init__(self, fpath):
        self._recoveryObject = RecoveryJsObject(self)  # RecoveryJsObject
        self._data = RestoreData()

        self._data = self.createFromFile(fpath)

    def isValid(self):
        return self._data.isValid()

    def restoreData(self):
        '''
        @return: RestoreData
        '''
        return self._data

    def clearRestoreData(self):
        crashedSession = QByteArray(self._data.crashedSession)
        self._data.clear()
        stream = QDataStream(crashedSession, QIODevice.ReadOnly)
        self._data = stream.readQVariant()

    def recoveryObject(self, page):
        '''
        @param: page WebPage
        @return: QObject
        '''
        self._recoveryObject.setPage(page)
        return self._recoveryObject

    @classmethod
    def validateFile(cls, fpath):
        '''
        @param: fpath QString
        '''
        data = cls.createFromFile(fpath)
        return data.isValid()

    @classmethod
    def createFromFile(cls, fpath):
        '''
        @param: fpath QString
        @return: data RestoreData
        '''
        data = RestoreData()
        if not QFile.exists(fpath):
            return data

        recoveryFile = QFile(fpath)
        if not recoveryFile.open(QIODevice.ReadOnly):
            return data

        stream = QDataStream(recoveryFile)

        version = stream.readInt()

        if version == const.sessionVersion:
            byteData = stream.readBytes()
            data = pickle.loads(byteData)
        else:
            print('WARNING: Unsupported session file version', version, 'path', fpath)
        return data
