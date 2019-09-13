from PyQt5.Qt import QObject
from PyQt5.Qt import QTimer
from PyQt5.Qt import pyqtSignal

from mc.common.models import (
    AutoFillDbModel,
    AutoFillEncryptedDbModel,
    AutoFillExceptionsDbModel,
    HistoryDbModel,
    SearchEnginesDbModel,
    IconsDbModel,
)

class SqlQueryJob(QObject):

    class Result:
        def __init__(self):
            self.error = None
            self.lastInsertId = None
            self.records = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self._query = None  # QuerySet?
        self._boundValues = []  # QVector<QVariant>
        self._error = None  # QSqlError
        self._lastInsertId = ''  # QVariant
        self._records = []  # QVector<QSqlRecord>

    def setQuery(self, query):
        self._query = query

    def lastInsertId(self):
        return self._lastInsertId

    def records(self):
        return self._records

    def start(self):

        def callBack():
            # TODO:
            pass

        QTimer.singleShot(0, callBack)

    # Q_SIGNALS:
    finished = pyqtSignal('PyQt_PyObject')  # job

class SqlDatabase(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._database = None

    def database(self):
        '''
        @brief: Returns database connection for current thread
        @return: QSqlDatabase
        '''
        return self._database

    def setDatabase(self, database):
        '''
        @brief: Sets database to be created for other threads
        @param: database QSqlDatabase
        '''
        self._database = database

        AutoFillDbModel._meta.database = database
        AutoFillEncryptedDbModel._meta.database = database
        AutoFillExceptionsDbModel._meta.database = database
        HistoryDbModel._meta.database = database
        SearchEnginesDbModel._meta.database = database
        IconsDbModel._meta.database = database

    _instance = None

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = SqlDatabase()
        return cls._instance
