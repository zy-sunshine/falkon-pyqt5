from PyQt5.QtWidgets import QTreeView
from PyQt5.Qt import pyqtSignal
from .BookmarkItem import BookmarkItem
from PyQt5.Qt import QPoint

class BookmarksTreeView(QTreeView):
    # enum ViewType
    BookmarksManagerViewType = 0
    BookmarksSidebarViewType = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bookmarks = None  # Bookmarks
        self._model = None  # BookmarksModel
        self._filter = None  # BookmarksFilterModel
        self._type = self.BookmarksManagerViewType  # ViewType

    def viewType(self):
        '''
        @return: ViewType
        '''
        pass

    def setViewType(self, type_):
        self._type = type_

    def selectedBookmark(self):
        '''
        @brief: Returns null if more than one (or zero) bookmarks are selected
        '''
        pass

    def selectedBookmarks(self):
        '''
        @brief: Returns all selected bookmarks
        '''
        pass

    def selectBookmark(self):
        pass

    def ensureBookmarkVisible(self, item):
        '''
        @brief: Expand up to root item
        '''
        pass

    # public Q_SLOTS:
    def search(self, string):
        '''
        @param: string QString
        '''
        pass

    # Q_SIGNALS:
    # Open bookmark in current tab
    bookmarkActivated = pyqtSignal(BookmarkItem)  # item
    # Open bookmark in new tab
    bookmarkCtrlActivated = pyqtSignal(BookmarkItem)  # item
    # Open bookmark in new window
    bookmarkShiftActivated = pyqtSignal(BookmarkItem)  # item
    # Context menu signal with point mapped to global
    contextMenuRequested = pyqtSignal(QPoint)  # point
    # If all bookmarks have been deselected, items is empty
    bookmarksSelected = pyqtSignal(list)  # QList<BookmarkItem> items

    # private Q_SLOTS:
    def _indexExpanded(self, parent):
        '''
        @param: parent QModelIndex
        '''
        pass

    def _indexCollapsed(self, parent):
        '''
        @param: parent QModelIndex
        '''
        pass

    # private:
    def _restoreExpandedState(self, parent):
        '''
        @param: parent QModelIndex
        '''
        pass

    # override
    def rowsInserted(self, parent, start, end):
        '''
        @param: parent QModelIndex
        @param: start int
        @param: end int
        '''
        pass

    # override
    def selectionChanged(self, selected, deselected):
        '''
        @param: selected QItemSelection
        @param: deselected QItemSelection
        '''
        pass

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # override
    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass
