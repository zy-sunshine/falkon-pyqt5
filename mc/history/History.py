from PyQt5.Qt import QObject
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QUrl
from PyQt5.Qt import pyqtSignal
from mc.app.Settings import Settings
from calendar import month_name
from .HistoryModel import HistoryModel

class History(QObject):

    class HistoryEntry:
        def __init__(self):
            self.id = 0
            self.count = 0
            self.date = QDateTime()
            self.url = QUrl()
            self.urlString = ''
            self.title = ''

    def __init__(self, parent):
        super().__init__(parent)
        self._isSaving = False
        self._model = None  # HistoryModel
        self.loadSettings()

    @classmethod
    def titleCaseLocalizedMonth(cls, month):
        index = month - 1
        if index < len(month_name):
            return month_name[index]
        else:
            print('warning: Month number(%s) out of range!' % month)
            return ''

    def model(self):
        '''
        @return: HistoryModel
        '''
        if not self._model:
            self._model = HistoryModel(self)
        return self._model

    def addHistoryEntryByView(self, view):
        '''
        @param: view WebView
        '''
        pass

    def addHistoryEntryByUrlAndTitle(self, url, title):
        '''
        @param: url QUrl
        @param: title QString
        '''
        pass

    def deleteHistoryEntryByIndex(self, index):
        '''
        @param: index int
        '''
        pass

    def deleteHistoryEntryByIndexList(self, list_):
        '''
        @param: list_ QList<int>
        '''
        pass

    def deleteHistoryEntryByUrl(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def deleteHistoryEntryByUrlAndTitle(self, url, title):
        '''
        @param: url QUrl
        @param: title QString
        '''
        pass

    def indexesFromTimeRange(self, start, end):
        '''
        @param: start qint64
        @param: end qint64
        @return: QList<int>
        '''
        pass

    def mostVisited(self):
        '''
        @return: QVector<HistoryEntry>
        '''
        pass

    def clearHistory(self):
        pass

    def isSaving(self):
        '''
        @return: bool
        '''
        pass

    def setSaving(self, state):
        '''
        @param: state bool
        '''
        pass

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        self._isSaving = settings.value('allowHistory', True, type=bool)
        settings.endGroup()

    def searchHistoryEntry(self, text):
        '''
        @param: text QString
        '''
        pass

    def getHistoryEntry(self, text):
        '''
        @param: text QString
        '''
        pass

    # Q_SIGNALS
    historyEntryAdded = pyqtSignal(HistoryEntry)  # entry
    historyEntryDeleted = pyqtSignal(HistoryEntry)  # entry
    historyEntryEdited = pyqtSignal(HistoryEntry)  # entry

    def resetHistory(self):
        pass

HistoryEntry = History.HistoryEntry
