from PyQt5.Qt import QStandardItemModel

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
    ) = range(Qt.UserRole + 1, 13)

    def __init__(self, parent=None):
        super().__init__(parent)

    def setCompletions(self, items):
        '''
        @param: items QList<QStandardItem>
        '''
        pass

    def addCompletions(self, items):
        '''
        @param: items QList<QStandardItem>
        '''
        pass

    def suggestionItems(self):
        '''
        @return: QList<QStandardItem>
        '''
        pass

    def createHistoryQuery(self, searchString, limit, exactMatch=False):
        '''
        @param: searchString QString
        @param: limit int
        @param: exactMatch bool
        '''
        pass

    def createDomainQuery(self, text):
        '''
        @param: text QString
        '''
        pass

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
        pass

    def _refreshTabPositions(self):
        pass
