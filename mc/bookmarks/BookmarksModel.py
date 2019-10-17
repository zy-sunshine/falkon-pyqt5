from PyQt5.Qt import QAbstractItemModel
from PyQt5.Qt import Qt
from PyQt5.Qt import QModelIndex
from PyQt5.Qt import QMimeData
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QSortFilterProxyModel
from PyQt5.Qt import QTimer
from .BookmarkItem import BookmarkItem

class BookmarksModel(QAbstractItemModel):
    # enum Roles
    TypeRole = Qt.UserRole + 1
    UrlRole = Qt.UserRole + 2
    UrlStringRole = Qt.UserRole + 3
    TitleRole = Qt.UserRole + 4
    IconRole = Qt.UserRole + 5
    DescriptionRole = Qt.UserRole + 6
    KeywordRole = Qt.UserRole + 7
    VisitCountRole = Qt.UserRole + 8
    ExpandedRole = Qt.UserRole + 9
    SidebarExpandedRole = Qt.UserRole + 10
    MaxRole = SidebarExpandedRole

    def __init__(self, root, bookmarks, parent=None):
        '''
        @param: root BookmarkItem
        @param: bookmarks Bookmarks
        @param: parent QObject
        '''
        super().__init__(parent)
        self._root = root  # BookmarkItem
        self._bookmarks = bookmarks  # Bookmarks

        if self._bookmarks:
            self._bookmarks.bookmarkChanged.connect(self._bookmarkChanged)

    def addBookmark(self, parent, row, item):
        '''
        @param: parent BookmarkItem
        @param: row int
        @param: item BookmarkItem
        '''
        assert(parent)
        assert(item)
        assert(row >= 0)
        assert(row <= len(parent.children()))

        self.beginInsertRows(self.indexByItem(parent), row, row)
        parent.addChild(item, row)
        self.endInsertRows()

    def removeBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item)
        assert(item.parent())

        idx = item.parent().children().index(item)

        self.beginRemoveRows(self.indexByItem(item.parent()), idx, idx)
        item.parent().removeChild(item)
        self.endRemoveRows()

    # override
    def flags(self, index):
        '''
        @param: index QModelIndex
        @return: Qt.ItemFlags
        '''
        item = self.item(index)

        if not index.isValid() or not item:
            return Qt.NoItemFlags

        # Qt.ItemFlag
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if item.isFolder():
            flags |= Qt.ItemIsDropEnabled

        if self._bookmarks and self._bookmarks.canBeModified(item):
            flags |= Qt.ItemIsDragEnabled

        return flags

    # override
    def data(self, index, role):  # noqa C901
        '''
        @param: index QModelIndex
        @param: role int
        '''
        # BookmarkItem
        item = self.item(index)

        if not item:
            return None

        if role == self.TypeRole:
            return item.type()
        elif role == self.UrlRole:
            return item.url()
        elif role == self.UrlStringRole:
            return item.urlString()
        elif role == self.TitleRole:
            return item.title()
        elif role == self.DescriptionRole:
            return item.description()
        elif role == self.KeywordRole:
            return item.keyword()
        elif role == self.VisitCountRole:
            return -1
        elif role == self.ExpandedRole:
            return item.isExpanded()
        elif role == self.SidebarExpandedRole:
            return item.isSidebarExpanded()
        elif role in(Qt.ToolTipRole, Qt.DisplayRole):
            column = index.column()
            if role == Qt.ToolTipRole:
                if column == 0 and item.isUrl():
                    return '%s\n%s' % (item.title(), item.url().toEncoded().data().decode())
            # fallthrough
            if column == 0:
                return item.title()
            elif column == 1:
                return item.url().toEncoded()
            else:
                return None
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                return item.icon()
            return None
        else:
            return None

    # override
    def headerData(self, section, orientation, role):
        '''
        @param: section int
        @param: orientation Qt.Orientation
        @param: role int
        '''
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return _('Title')
            elif section == 1:
                return _('Address')
        return super().headerData(section, orientation, role)

    # override
    def rowCount(self, parent):
        '''
        @param: parent QModelIndex
        '''
        if parent.column() > 0:
            return 0

        item = self.item(parent)
        return len(item.children())

    # override
    def columnCount(self, parent):
        '''
        @param: parent QModelIndex
        '''
        if parent.column() > 0:
            return 0
        return 2

    # override
    def hasChildren(self, parent):
        '''
        @param: parent QModelIndex
        '''
        item = self.item(parent)
        return not not item.children()

    # override
    def supportedDropAction(self):
        '''
        @return: Qt.DropActions
        '''
        return Qt.CopyAction | Qt.MoveAction

    MIMETYPE = 'application/app.bookmarks'
    # override
    def mimeTypes(self):
        '''
        @return: QStringList
        '''
        types = []  # QStringList
        types.append(self.MIMETYPE)
        return types

    # override
    def mimeData(self, indexes):
        '''
        @param: indexes QModelIndexList
        @return: QMimeData
        '''
        mimeData = QMimeData()
        self._tmpMimeItems = []
        for index in indexes:
            # If item's parent (=folder) is also selected, we will just move the
            # whole folder
            if index.isValid() and index.column() == 0 and index.parent() not in indexes:
                item = index.internalPointer()
                assert(isinstance(item, BookmarkItem))
                self._tmpMimeItems.append(item)
        mimeData.setData(self.MIMETYPE, b'')
        return mimeData

    # override
    def dropMimeData(self, data, action, row, column, parent):
        '''
        @param: data QMimeData
        @param: action Qt.DropAction
        @param: row int
        @param: column int
        @param: parent QModelIndex
        '''
        if action == Qt.IgnoreAction:
            del self._tmpMimeItems
            return True

        if not self._bookmarks or not data.hasFormat(self.MIMETYPE) or \
                not parent.isValid():
            del self._tmpMimeItems
            return False

        parentItem = self.item(parent)
        assert(parentItem.isFolder())

        items = self._tmpMimeItems
        del self._tmpMimeItems

        for item in items:
            assert(item != self._bookmarks.rootItem())

            # Cannot move bookmark to itself
            if item == parentItem:
                return False

        row = max(row, 0)

        for item in items:
            # If we are moving an item through the folder and item is above the
            # row to insert, we must decrease row by one (by the dropped folder)
            if item.parent() == parentItem and item.parent().children().index(item) < row:
                row -= 1
            self._bookmarks.removeBookmark(item)
            self._bookmarks.insertBookmark(parentItem, row, item)
            row += 1

        return True

    # override
    def parent(self, child):
        '''
        @param: child QModelIndex
        @return: QModelIndex
        '''
        if not child.isValid():
            return QModelIndex()

        item = self.item(child)
        return self.indexByItem(item.parent())

    # override
    def index(self, row, column, parent=QModelIndex()):
        '''
        @param: row int
        @param: column int
        @param: parent QModelIndex
        @return: QModelIndex
        '''
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        # BookmarkItem
        parentItem = self.item(parent)
        return self.createIndex(row, column, parentItem.children()[row])

    def indexByItem(self, item, column=0):
        '''
        @param: item BookmarkItem
        @return: QModelIndex
        '''
        parent = item.parent()
        if not parent:
            return QModelIndex()

        return self.createIndex(parent.children().index(item), column, item)

    def item(self, index):
        '''
        @param: index QModelIndex
        @return: BookmarkItem
        '''
        item = index.internalPointer()
        if item and isinstance(item, BookmarkItem):
            return item
        else:
            return self._root

    # private Q_SLOTS:
    def _bookmarkChanged(self, item):
        '''
        @param: item BookmarkItem
        '''
        idx = self.indexByItem(item)
        self.dataChanged.emit(idx, idx)

class BookmarksFilterModel(QSortFilterProxyModel):
    def __init__(self, parent):
        '''
        @param: parent QAbstractItemModel
        '''
        super().__init__(parent)
        self._pattern = ''
        self._filterTimer = None  # QTimer
        self.setSourceModel(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self._filterTimer = QTimer(self)
        self._filterTimer.setSingleShot(True)
        self._filterTimer.setInterval(300)

        self._filterTimer.timeout.connect(self._startFiltering)

    # public Q_SLOTS:
    def setFilterFixedString(self, pattern):
        self._pattern = pattern
        self._filterTimer.start()

    # protected:
    # override
    def filterAcceptsRow(self, sourceRow, sourceParent):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        if index.data(BookmarksModel.TypeRole) == BookmarkItem.Folder:
            return True

        pattern = self._pattern
        title = index.data(BookmarksModel.TitleRole)
        url = index.data(BookmarksModel.UrlStringRole)
        desc = index.data(BookmarksModel.DescriptionRole)
        keyword = index.data(BookmarksModel.KeywordRole)
        if self.filterCaseSensitivity() == Qt.CaseInsensitive:
            pattern = pattern.lower()
            title = title.lower()
            url = url.lower()
            desc = desc.lower()
            keyword = keyword.lower()
        return pattern in title or pattern in url or pattern in desc or \
            pattern == keyword

    # private Q_SLOTS:
    def _startFiltering(self):
        super().setFilterFixedString(self._pattern)

class BookmarksButtonMimeData(QMimeData):
    def __init__(self):
        super().__init__()
        self._item = None  # BookmarkItem

    def item(self):
        '''
        @return: BookmarkItem
        '''
        return self._item

    def setBookmarkItem(self, item):
        '''
        @param: item BookmarkItem
        '''
        self._item = item

    # override
    def hasFormat(self, format_):
        '''
        @param: format_ QString
        @return: true
        '''
        return self.mimeType() == format_

    # override
    def formats(self):
        '''
        @return: QStringList
        '''
        return [self.mimeType(), ]

    @classmethod
    def mimeType(cls):
        '''
        @return: QString
        '''
        return 'application/app.bookmarktoolbutton.bookmarkitem'
