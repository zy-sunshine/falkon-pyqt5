from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QPoint
from PyQt5.Qt import QModelIndex
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.Qt import QItemSelectionModel
from PyQt5.Qt import Qt
from PyQt5.Qt import QApplication
from mc.common.globalvars import gVar
from .BookmarkItem import BookmarkItem
from .BookmarksModel import BookmarksFilterModel, BookmarksModel
from .BookmarksItemDelegate import BookmarksItemDelegate

class BookmarksTreeView(QTreeView):
    # enum ViewType
    BookmarksManagerViewType = 0
    BookmarksSidebarViewType = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bookmarks = gVar.app.bookmarks()  # Bookmarks
        self._model = self._bookmarks.model()  # BookmarksModel
        self._filter = BookmarksFilterModel(self._model)  # BookmarksFilterModel
        self._type = self.BookmarksManagerViewType  # ViewType

        self.setModel(self._filter)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setUniformRowHeights(True)
        self.setDropIndicatorShown(True)
        self.setAllColumnsShowFocus(True)
        self.setItemDelegate(BookmarksItemDelegate(self))
        self.header().resizeSections(QHeaderView.ResizeToContents)

        self.expanded.connect(self._indexExpanded)
        self.collapsed.connect(self._indexCollapsed)

    def viewType(self):
        '''
        @return: ViewType
        '''
        return self._type

    def setViewType(self, type_):
        self._type = type_

        if self._type == self.BookmarksManagerViewType:
            self.setColumnHidden(1, False)
            self.setHeaderHidden(False)
            self.setMouseTracking(False)
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        elif self._type == self.BookmarksSidebarViewType:
            self.setColumnHidden(1, True)
            self.setHeaderHidden(True)
            self.setMouseTracking(True)
            self.setSelectionMode(QAbstractItemView.SingleSelection)

        self._restoreExpandedState(QModelIndex())

    def selectedBookmark(self):
        '''
        @brief: Returns null if more than one (or zero) bookmarks are selected
        '''
        items = self.selectedBookmarks()
        return len(items) == 1 and items[0] or None

    def selectedBookmarks(self):
        '''
        @brief: Returns all selected bookmarks
        '''
        items = []  # QList<BookmarkItem>

        for index in self.selectionModel().selectedRows():
            # BookmarkItem
            item = self._model.item(self._filter.mapToSource(index))
            items.append(item)
        return items

    def selectBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        col0 = self._filter.mapFromSource(self._model.indexByItem(item, 0))
        col1 = self._filter.mapFromSource(self._model.indexByItem(item, 1))

        selectionModel = self.selectionModel()
        selectionModel.clearSelection()
        selectionModel.select(col0, QItemSelectionModel.Select)
        selectionModel.select(col1, QItemSelectionModel.Select)

    def ensureBookmarkVisible(self, item):
        '''
        @brief: Expand up to root item
        '''
        # QModelIndex
        index = self._filter.mapFromSource(self._model.indexByItem(item))
        parent = self._filter.parent(index)

        while parent.isValid():
            self.setExpanded(parent, True)
            parent = self._filter.parent(parent)

    # public Q_SLOTS:
    def search(self, string):
        '''
        @param: string QString
        '''
        self._filter.setFilterFixedString(string)

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
        item = self._model.item(self._filter.mapToSource(parent))

        if self._type == self.BookmarksManagerViewType:
            item.setExtpanded(True)
        elif self._type == self.BookmarksSidebarViewType:
            item.setSidebarExpanded(True)

    def _indexCollapsed(self, parent):
        '''
        @param: parent QModelIndex
        '''
        item = self._model.item(self._filter.mapToSource(parent))

        if self._type == self.BookmarksManagerViewType:
            item.setExtpanded(False)
        elif self._type == self.BookmarksSidebarViewType:
            item.setSidebarExpanded(False)

    # private:
    def _restoreExpandedState(self, parent):
        '''
        @param: parent QModelIndex
        '''
        for idx in range(self._filter.rowCount(parent)):
            # QModeLIndex
            index = self._filter.index(idx, 0, parent)
            item = self._model.item(self._filter.mapToSource(index))
            if self._type == self.BookmarksManagerViewType:
                self.setExpanded(index, item.isExpanded())
            else:
                self.setExpanded(index, item.isSidebarExpanded())
            self._restoreExpandedState(index)

    # override
    def rowsInserted(self, parent, start, end):
        '''
        @param: parent QModelIndex
        @param: start int
        @param: end int
        '''
        self._restoreExpandedState(parent)
        super().rowsInserted(parent, start, end)

    # override
    def selectionChanged(self, selected, deselected):
        '''
        @param: selected QItemSelection
        @param: deselected QItemSelection
        '''
        self.bookmarksSelected.emit(self.selectedBookmarks())

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        self.contextMenuRequested.emit(self.viewport().mapToGlobal(event.pos()))

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        print('mouseMoveEvent')
        super().mouseMoveEvent(event)

        if self._type == self.BookmarksSidebarViewType:
            cursor = Qt.ArrowCursor
            if event.buttons() == Qt.NoButton:
                # QModelIndex
                index = self.indexAt(event.pos())
                if index.isValid() and index.data(BookmarksModel.TypeRole) == BookmarkItem.Url:
                    cursor = Qt.PointingHandCursor
            self.viewport().setCursor(cursor)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        print('mousePressEvent')
        super().mousePressEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            index = self.indexAt(event.pos())
            # Qt::MouseButtons
            buttons = event.buttons()
            # Qt::KeyboardModifiers
            modifiers = event.modifiers()

            if index.isValid():
                item = self._model.item(self._filter.mapToSource(index))

                if buttons == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                    self.bookmarkShiftActivated.emit(item)
                elif buttons == Qt.MiddleButton or (buttons == Qt.LeftButton and
                        modifiers == Qt.ControlModifier):
                    self.bookmarkCtrlActivated.emit(item)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        print('mouseReleaseEvent')
        super().mouseReleaseEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            # QModelIndex
            index = self.indexAt(event.pos())

            if index.isValid():
                item = self._model.item(self._filter.mapToSource(index))

                # Activate bookmarks with single mouse click in Sidebar
                if self._type == self.BookmarksSidebarViewType and \
                        event.button() == Qt.LeftButton and \
                        event.modifiers() == Qt.NoModifier:
                    self.bookmarkActivated.emit(item)

    # override
    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        print('mouseDoubleClickEvent')
        super().mouseDoubleClickEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            # QModelIndex
            index = self.indexAt(event.pos())

            if index.isValid():
                item = self._model.item(self._filter.mapToSource(index))

                # Qt::MouseButtons
                buttons = event.buttons()
                # Qt::KeyboardModifiers
                modifiers = QApplication.keyboardModifiers()

                if buttons == Qt.LeftButton and modifiers == Qt.NoModifier:
                    self.bookmarkActivated.emit(item)
                elif buttons == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                    self.bookmarkShiftActivated.emit(item)

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        print('keyPressEvent')
        super().keyPressEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            # QModelIndex
            index = self.selectionModel().selectedRows()[0]
            item = self._model.item(self._filter.mapToSource(index))
            key = event.key()
            modifiers = event.modifiers()

            if key in (Qt.Key_Return, Qt.Key_Enter):
                if item.isFolder() and (modifiers == Qt.NoModifier or
                        modifiers == Qt.KeypadModifier):
                    self.setExpanded(index, not self.isExpanded(index))
                else:
                    if modifiers == Qt.NoModifier or modifiers == Qt.KeypadModifier:
                        self.bookmarkActivated.emit(item)
                    elif modifiers == Qt.ControlModifier:
                        self.bookmarkCtrlActivated.emit(item)
                    elif modifiers == Qt.ShiftModifier:
                        self.bookmarkShiftActivated.emit(item)
