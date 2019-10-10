from PyQt5.Qt import QStandardItemModel
from PyQt5.Qt import Qt
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QImage
from PyQt5.Qt import QIcon
from mc.tools.IconProvider import IconProvider
from mc.common.models import HistoryDbModel
from mc.common.globalvars import gVar

class LocationCompleterModel(QStandardItemModel):
    # enum Role
    (
        IdRole,
        TitleRole,
        UrlRole,
        CountRole,
        HistoryRole,
        BookmarkRole,
        BookmarkItemRole,
        SearchStringRole,
        TabPositionWindowRole,
        TabPositionTabRole,
        ImageRole,
        VisitSearchItemRole,
        SearchSuggestionRole,
    ) = range(Qt.UserRole + 1, Qt.UserRole + 14)

    def __init__(self, parent=None):
        super().__init__(parent)

    def setCompletions(self, items):
        '''
        @param: items QList<QStandardItem>
        '''
        self.clear()
        self.addCompletions(items)

    def addCompletions(self, items):
        '''
        @param: items QList<QStandardItem>
        '''
        for item in items:
            img = item.data(self.ImageRole)
            if not img:
                img = QImage()
            pixmap = QPixmap.fromImage(img)
            item.setIcon(QIcon(pixmap))
            self._setTabPosition(item)
            if item.icon().isNull():
                item.setIcon(IconProvider.emptyWebIcon())
            self.appendRow([item])

    def suggestionItems(self):
        '''
        @return: QList<QStandardItem>
        '''
        items = []  # QList<QStandardItem>
        for idx in range(self.rowCount()):
            item = self.item(idx)
            if item.data(self.SearchSuggestionRole):
                items.append(item)
        return items

    def createHistoryQuery(self, searchString, limit, exactMatch=False):
        '''
        @param: searchString QString
        @param: limit int
        @param: exactMatch bool
        '''
        searchList = []  # QStringList
        qs = HistoryDbModel.select()
        if exactMatch:
            qs = qs.where(HistoryDbModel.title.contains(searchString) |
                    HistoryDbModel.url.contains(searchString))
        else:
            searchList = [ item.strip() for item in searchString.split(' ') ]
            searchList = [ item for item in searchList if item ]
            conds = []
            for item in len(searchList):
                conds.append(
                    (HistoryDbModel.title.contains(item) |
                    HistoryDbModel.url.contains(item))
                )
            from peewee import operator
            from functools import reduce
            qs = qs.where(reduce(operator.and_, conds))

        qs = qs.order_by(HistoryDbModel.date.desc()).limit(limit)

        return qs

    def createDomainQuery(self, text):
        '''
        @param: text QString
        '''
        if not text or text == 'www.':
            return HistoryDbModel.select()

        withoutWww = text.startswith('w') and not text.startswith('www.')
        qs = HistoryDbModel.select()
        if withoutWww:
            qs = qs.where(~HistoryDbModel.url.startswith('http://www.') &
                ~HistoryDbModel.url.startswith('https://www.') &
                    (HistoryDbModel.url.startswith('http://%s' % text) |
                    HistoryDbModel.url.startswith('https://%s' % text))
            )
        else:
            qs = qs.where(HistoryDbModel.url.startswith('http://%s' % text) |
                HistoryDbModel.url.startswith('https://%s' % text) |
                    (HistoryDbModel.url.startswith('http://www.%s' % text |
                    HistoryDbModel.url.startswith('https://www.%s' % text)))
            )

        qs = qs.order_by(HistoryDbModel.date.desc()).limit(1)
        return qs

    # private:
    # enum Type
    HistoryAddBookmarks = 0
    History = 1
    Bookmarks = 2
    Nothing = 4

    def _setTabPosition(self, item):
        '''
        @param: item QStandardItem
        '''
        assert(item)

        item.setData(-1, self.TabPositionTabRole)

        if not gVar.appSettings.showSwitchTab or item.data(self.VisitSearchItemRole):
            return

        # QUrl
        url = item.data(self.UrlRole)
        # QList<BrowserWindow>
        windows = gVar.app.windows()

        for window in windows:
            tabs = window.tabWidget().allTabs()
            for idx, tab in enumerate(tabs):
                if tab.url() == url:
                    item.setData(window, self.TabPositionWindowRole)
                    item.setData(idx, self.TabPositionTabRole)
                    return

    def _refreshTabPositions(self):
        for row in range(self.rowCount()):
            item = self.item(row)
            if item:
                self._setTabPosition(item)
