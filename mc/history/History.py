from PyQt5.Qt import QObject
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QUrl
from PyQt5.Qt import pyqtSignal
from mc.app.Settings import Settings
from calendar import month_name
from .HistoryModel import HistoryModel
from mc.common.models import HistoryDbModel
from mc.common.models import IconsDbModel
from mc.common.globalvars import gVar
from datetime import datetime

class History(QObject):

    class HistoryEntry:
        def __init__(self):
            self.id = 0
            self.count = 0
            self.date = QDateTime()
            self.url = QUrl()
            self.urlString = ''
            self.title = ''

        def fillDbobj(self, dbobj):
            for field in ('id', 'count', 'urlString', 'title'):
                setattr(dbobj, field, getattr(self, field))
            dbobj.date = self.date.toMSecsSinceEpoch()
            dbobj.url = self.url.toString()

        @classmethod
        def CreateFromDbobj(cls, dbobj):
            entry = cls()
            entry.id = dbobj.id
            entry.count = dbobj.id
            entry.date = QDateTime.fromMSecsSinceEpoch(dbobj.date)
            entry.url = QUrl(dbobj.url)
            entry.urlString = entry.url.toEncoded().data().decode()
            entry.title = dbobj.title
            return entry

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
        if not self._isSaving:
            return

        url = view.url()
        title = view.title()

        self.addHistoryEntryByUrlAndTitle(url, title)

    def addHistoryEntryByUrlAndTitle(self, url, title):
        '''
        @param: url QUrl
        @param: title QString
        '''
        if not self._isSaving:
            return

        schemes = ['http', 'https', 'ftp', 'file']

        if url.scheme() not in schemes:
            return

        if not title:
            title = _('Empty Page')

        def addEntryFunc():
            dbobj = HistoryDbModel.select().where(HistoryDbModel.url == url.toString()).first()
            if dbobj:
                # update
                before = self.HistoryEntry()
                before.id = dbobj.id
                before.count = dbobj.count
                before.date = QDateTime.fromMSecsSinceEpoch(dbobj.date)
                before.url = url
                before.urlString = before.url.toEncoded().data().decode()
                before.title = dbobj.title

                after = self.HistoryEntry()
                after.count = dbobj.count + 1
                after.date = QDateTime.currentDateTime()
                after.title = title
                after.url = url
                after.urlString = after.url.toEncoded().data().decode()
                after.fillDbobj(dbobj)
                dbobj.save()

                self.historyEntryEdited.emit(before, after)
            else:
                # insert
                dbobj = HistoryDbModel.create(**{
                    'count': 1,
                    'date': int(datetime.now().timestamp()),
                    'url': url.toString(),
                    'title': title,
                })
                entry = self.HistoryEntry.CreateFromDbobj(dbobj)
                self.historyEntryAdded.emit(entry)

        gVar.executor.submit(addEntryFunc)

    def deleteHistoryEntry(self, indexOrList):
        '''
        @param: indexOrList int/list/tuple
        '''
        if not isinstance(indexOrList, (list, tuple)):
            list_ = []
            list_.append(indexOrList)
        else:
            list_ = indexOrList

        self._deleteHistoryEntryByIndexList(list_)

    def _deleteHistoryEntryByIndexList(self, list_):
        '''
        @param: list_ QList<int>
        '''

        dbobjs = list(HistoryDbModel.select().where(HistoryDbModel.id.in_(list_)))
        HistoryDbModel.delete().where(HistoryDbModel.id.in_(list_)).execute()
        urls = [ QUrl(obj.url).toEncoded(QUrl.RemoveFragment) for obj in dbobjs ]
        IconsDbModel.delete().where(IconsDbModel.url.in_(urls)).execute()
        for dbobj in dbobjs:
            entry = self.HistoryEntry.CreateFromDbobj(dbobj)
            self.historyEntryDeleted.emit(entry)

    def deleteHistoryEntryByUrl(self, url):
        '''
        @param: url QUrl
        '''
        items = HistoryDbModel.select(columns=['id']).where(HistoryDbModel.url == url).dicts()
        import ipdb; ipdb.set_trace()
        ids = [ item['id'] for item in dicts ]
        self._deleteHistoryEntryByIndexList(ids)

    def deleteHistoryEntryByUrlAndTitle(self, url, title):
        '''
        @param: url QUrl
        @param: title QString
        '''
        items = HistoryDbModel.select(columns=['id']).where(HistoryDbModel.url == url,
                HistoryDbModel.title == title).dicts()
        import ipdb; ipdb.set_trace()
        ids = [ item['id'] for item in dicts ]
        self._deleteHistoryEntryByIndexList(ids)

    def indexesFromTimeRange(self, start, end):
        '''
        @param: start qint64
        @param: end qint64
        @return: QList<int>
        '''
        pass

    def mostVisited(self, count):
        '''
        @param: count int
        @return: QVector<HistoryEntry>
        '''
        result = []
        for dbobj in HistoryDbModel.select().order_by(HistoryDbModel.count.desc()).limit(count):
            entry = self.HistoryEntry()
            entry.count = dbobj.count
            entry.date = QDateTime.fromMSecsSinceEpoch(dbobj.date)
            entry.id = dbobj.id
            entry.title = dbobj.title
            entry.url = QUrl(dbobj.url)
            result.append(entry)
        return result

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
    historyEntryEdited = pyqtSignal(HistoryEntry, HistoryEntry)  # before, after

    resetHistory = pyqtSignal()

HistoryEntry = History.HistoryEntry
