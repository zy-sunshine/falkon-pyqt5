from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QUrl
from PyQt5.Qt import QDateTime
from mc.common.globalvars import gVar
from .LocationCompleterModel import LocationCompleterModel
from mc.tools.IconProvider import IconProvider
from mc.common.models import HistoryDbModel

class LocationCompleterRefreshJob(QObject):
    def __init__(self, searchString):
        super().__init__()
        self._timestamp = QDateTime.currentMSecsSinceEpoch()  # qint64
        self._searchString = searchString
        self._domainCompletion = ''
        self._items = []  # QList<QStandardItem>
        self._jobCancelled = False

        def func():
            try:
                self._runJob()
            finally:
                self._slotFinished()
        gVar.executor.submit(func)

    def timestamp(self):
        '''
        @brief: Timestamp when the job has create
        @return: qint64
        '''
        return self._timestamp

    def searchString(self):
        '''
        @return: QString
        '''
        return self._searchString

    def isCanceled(self):
        '''
        @return: bool
        '''
        return self._jobCancelled

    def completions(self):
        '''
        @return: QList<QStandardItem>
        '''
        return self._items

    def domainCompletion(self):
        '''
        @return: QString
        '''
        return self._domainCompletion

    # Q_SIGNALS
    finished = pyqtSignal()

    # private Q_SLOTS:
    def _slotFinished(self):
        self.finished.emit()

    def jobCancelled(self):
        self._jobCancelled = True

    # private:
    # enum Type
    HistoryAndBookmarks = 0
    History = 1
    Bookmarks = 2
    Nothing = 4

    def _runJob(self):
        if self._jobCancelled or gVar.app.isClosing():
            return

        if not self._searchString:
            self._completeMostVisited()
        else:
            self._completeFromHistory()

        # Load all icons into QImage
        for item in self._items:
            if self._jobCancelled:
                return

            # QUrl
            url = item.data(LocationCompleterModel.UrlRole)
            item.setData(IconProvider.imageForUrl(url), LocationCompleterModel.ImageRole)

        if self._jobCancelled:
            return

        # Get domain completion
        if self._searchString and gVar.appSettings.useInlineCompletion:
            domainQuery = LocationCompleterModel.createDomainQuery(self._searchString)
            history = domainQuery.first()
            if history:
                self._domainCompletion = QUrl(history.url).host()

        if self._jobCancelled:
            return

        # Add search/visit item
        if self._searchString:
            item = QStandardItem()
            item.setText(self._searchString)
            item.setData(self._searchString, LocationCompleterModel.UrlRole)
            item.setData(self._searchString, LocationCompleterModel.SearchStringRole)
            item.setData(True, LocationCompleterModel.VisitSearchItemRole)
            if self._domainCompletion:
                url = QUrl('http://%s' % self._domainCompletion)
                item.setData(IconProvider.imageForDomain(url), LocationCompleterModel.ImageRole)
            self._items.insert(0, item)

    def _completeFromHistory(self):
        urlList = []  # QList<QUrl>
        showType = gVar.appSettings.showLocationSuggestions

        # Search in bookmarks
        if showType == self.HistoryAndBookmarks or showType == self.Bookmarks:
            bookmarksLimit = 20
            bookmarks = gVar.app.bookmarks().searchBookmarksByString(
                self._searchString, bookmarksLimit)

            for bookmark in bookmarks:
                assert(bookmark.isUrl())

                # Keyword bookmark replaces visit/search item
                if bookmark.keyword() == self._searchString:
                    continue

                item = QStandardItem()
                item.setText(bookmark.url().toEncoded().data().decode())
                item.setData(-1, LocationCompleterModel.IdRole)
                item.setData(bookmark.title(), LocationCompleterModel.TitleRole)
                item.setData(bookmark.url(), LocationCompleterModel.UrlRole)
                item.setData(bookmark.visitCount(), LocationCompleterModel.CountRole)
                item.setData(True, LocationCompleterModel.BookmarkRole)
                item.setData(bookmark, LocationCompleterModel.BookmarkItemRole)
                item.setData(self._searchString, LocationCompleterModel.SearchStringRole)

                urlList.append(bookmark.url())
                self._items.append(item)

        # Sort by count
        self._items.sort(key=lambda item: item.data(LocationCompleterModel.CountRole), reverse=True)

        # Search in history
        if showType == self.HistoryAndBookmarks or showType == self.History:
            historyLimit = 20
            qs = LocationCompleterModel.createHistoryQuery(self._searchString, historyLimit)

            for history in qs:
                url = QUrl(history.url)

                if url in urlList:
                    continue

                item = QStandardItem()
                item.setText(url.toEncoded().data().decode())
                item.setData(history.id, LocationCompleterModel.IdRole)
                item.setData(history.title, LocationCompleterModel.TitleRole)
                item.setData(url, LocationCompleterModel.UrlRole)
                item.setData(history.count, LocationCompleterModel.CountRole)
                item.setData(True, LocationCompleterModel.HistoryRole)
                item.setData(self._searchString, LocationCompleterModel.SearchStringRole)

                self._items.append(item)

    def _completeMostVisited(self):
        qs = HistoryDbModel.select().order_by(HistoryDbModel.count.desc()).limit(15)
        for history in qs:
            item = QStandardItem()
            url = QUrl(history.url)

            item.setText(url.toEncoded().data().decode())
            item.setData(history.id, LocationCompleterModel.IdRole)
            item.setData(history.title, LocationCompleterModel.TitleRole)
            item.setData(url, LocationCompleterModel.UrlRole)
            item.setData(True, LocationCompleterModel.HistoryRole)

            self._items.append(item)

    def createDomainCompletion(self, completion):
        '''
        @param completion QString
        @return: QString
        '''
        # Make sure search string and completion matches
        if self._searchString.startswith('www.') and not completion.startswith('www.'):
            return 'www.%s' % completion

        if not self._searchString.startswith('www.') and completion.startswith('www.'):
            return completion[4:]

        return completion
