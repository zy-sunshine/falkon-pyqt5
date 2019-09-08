from sys import stderr
from PyQt5.Qt import QAbstractProxyModel
from PyQt5.Qt import QModelIndex
from PyQt5.Qt import Qt
from .TabModel import TabModel

class TabMruModelItem(object):
    def __init__(self, tab=None, index=QModelIndex()):
        self._tab = tab
        self._sourceIndex = index
        self._children = []  # QVector<TabMruModelItem>

class TabMruModel(QAbstractProxyModel):
    def __init__(self, window, parent=None):
        super(TabMruModel, self).__init__(parent)
        self._window = window
        self._root = None
        self._items = {}  # QHash<WebTab*, TabMruModelItem*>
        self.sourceModelChanged.connect(self._init)

    def tabIndex(self, tab):
        '''
        @param: tab WebTab
        @return: QModelIndex
        '''
        item = self._items.get(tab)
        if not item:
            return QModelIndex()
        else:
            return self.createIndex(self._root.children.index(item), 0, item)

    def tab(self, index):
        '''
        @param: index QModelIndex
        @return: WebTab
        '''
        it = self._item(index)
        if not it: return None
        else: return it.tab

    def flags(self, index):
        '''
        @param: index QModelIndex
        @return: Q::ItemFlags
        '''
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def rowCount(self, parent):
        '''
        @param: parent QModelIndex
        '''
        if parent.isValid():
            return 0
        return len(self._items)

    def columnCount(self, parent):
        '''
        @param: parent QModelIndex
        '''
        if parent.column() > 0:
            return 0
        return 1

    def parent(self, index):
        '''
        @param: index QModelIndex
        @return: QModelIndex
        '''
        return QModelIndex()

    def index(self, row, column, parent=QModelIndex()):
        '''
        @param: row int
        @param: column int
        @return: QModelIndex
        '''
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column, self._root.children[row])

    def mapFromSource(self, sourceIndex):
        '''
        @param: sourceIndex QModelIndex
        @return: QModelIndex
        '''
        # TODO: return tabIndex(sourceIndex.data(TabModel::WebTabRole).value<WebTab*>());
        return self.tabIndex(sourceIndex.data(TabModel.WebTabRole))

    def mapToSource(self, proxyIndex):
        '''
        @param: proxyIndex QModelIndex
        @return: QModelIndex
        '''
        it = self._item(proxyIndex)
        if not it:
            return QModelIndex()
        return it.sourceIndex

    def _init(self):
        del self._root
        self._items.clear()
        self._root = TabMruModelItem()
        self._sourceRowsInserted(QModelIndex(), 0, self.sourceModel().rowCount())
        self._currentTabChanged(self._window.tabWidget().currentIndex())

        self._window.tabWidget().currentChanged.connect(self._currentTabChanged, Qt.UniqueConnection)
        self.sourceModel().dataChanged.connect(self._sourceDataChanged, Qt.UniqueConnection)
        self.sourceModel().rowsInserted.connect(self._sourceRowsInserted, Qt.UniqueConnection)
        self.sourceModel().rowsAboutToBeRemoved.connect(self._sourceRowsAboutToBeRemoved, Qt.UniqueConnection)
        self.sourceModel().modelReset.connect(self._sourceReset, Qt.UniqueConnection)

    def _index(self, item):
        '''
        @param: item TabMruModelItem
        @return: QModelIndex
        '''
        if not item or item == self._root:
            return QModelIndex()
        return self.createIndex(self._root.children.index(item), 0, item)

    def _item(eslf, index):
        '''
        @param: index QModelIndex
        @return: TabMruModelItem
        '''
        # TODO: return static_cast<TabMruModelItem*>(index.internalPointer())
        return index.internalPointer()

    def _currentTabChanged(self, index):
        it = self._item(self.mapFromSource(self.sourceModel().index(index, 0)))
        if not it:
            return
        from_ = self._root.children.index(it)
        if from_ == 0:
            return
        if not self.beginMoveRows(QModelIndex(), from_, from_, QModelIndex(), 0):
            print('Invalid beginMoveRows %s' % from_, file=stderr)
            return
        self._root.children.pop(from_)
        self._root.children.insert(0, it)
        self.endMoveRows()

    def _sourceDataChanged(self, topLeft, bottomRight, roles):
        '''
        @param: topLeft QModelIndex
        @param: bottomRight QModelIndex
        @param: roles QVector<int>
        '''
        self.dataChanged.emit(self.mapFromSource(topLeft), self.mapFromSource(bottomRight), roles)

    def _sourceRowsInserted(self, parent, start, end):
        '''
        @param: parent QModelIndex
        @param: start int
        @param: end int
        '''
        if start == end: return
        for idx in range(start, end + 1):
            index = self.sourceModel().index(idx, 0, parent)
            # TODO: WebTab *tab = index.data(TabModel::WebTabRole).value<WebTab*>()
            tab = index.data(TabModel.WebTabRole)
            if tab:
                self.beginInsertRows(QModelIndex(), len(self._item), len(self._items))
                item = TabMruModelItem(tab, index)
                self._items[tab] = item
                self._root.children.append(item)
                self.endInsertRows()

    def _sourceRowsAboutToBeRemoved(self, parent, start, end):
        '''
        @param: parent QModelIndex
        @param: start int
        @param: end int
        '''
        for idx in range(start, end+1):
            index = self.sourceModel().index(idx, 0, parent)
            it = self._item(self.mapFromSource(index))
            if it:
                idx = self._root.children.index(it)
                self.beginRemoveRows(QModelIndex(), idx, idx)
                self._items.remove(it.tab)
                self._root.children.pop(idx)
                del it
                self.endRemoveRows()

    def _sourceReset(self):
        self.beginResetModel()
        self._init()
        self.endResetModel()
