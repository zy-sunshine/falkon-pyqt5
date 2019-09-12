from sys import stderr
from PyQt5.Qt import QAbstractListModel
from PyQt5.Qt import Qt
from PyQt5.Qt import QModelIndex
from PyQt5.Qt import QVariant
from PyQt5.Qt import QMimeData
from mc.common import const

class TabModelMimeData(QMimeData):
    def __init__(self):
        self._tab = None

    def tab(self):
        return self._tab

    def setTab(self, tab):
        self._tab = tab

    def hasFormat(self, format_):
        return self.mimeType() == format_

    def formats(self):
        return [self.mimeType()]

    def mimeType(self):
        return 'application/%s.tabmodel/tab' % const.APPNAME

class TabModel(QAbstractListModel):
    # enum Roles
    WebTabRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    IconRole = Qt.UserRole + 3
    PinnedRole = Qt.UserRole + 4
    RestoredRole = Qt.UserRole + 5
    CurrentTabRole = Qt.UserRole + 6
    LoadingRole = Qt.UserRole + 7
    AudioPlayingRole = Qt.UserRole + 8
    AudioMutedRole = Qt.UserRole + 9
    BackgroundActivityRole = Qt.UserRole + 10

    def __init__(self, window, parent=None):
        super(TabModel, self).__init__(parent)
        self._window = window
        self._tabs = []  # WebTabs
        self._init()

    def tabIndex(self, tab):
        '''
        @param: tab WebTab
        @return: QModelIndex
        '''
        try:
            idx = self._tabs.index(tab)
        except ValueError:
            return QModelIndex()
        else:
            return self.index(idx)

    def tab(self, index):
        '''
        @param: index QModelIndex
        @return: WebTab
        '''
        self._tabs[index.row()]

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._tabs)

    def flags(self, index):
        '''
        @param: index QModelIndex
        @return: Qt::ItemFlags
        '''
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled

    def data(self, index, role=Qt.DisplayRole):  # noqa C901
        '''
        @param: index QModelIndex
        @return: QVariant
        '''
        row = index.row()
        if row < 0 or row > len(self._tabs):
            return QVariant()

        tab = self.tab(index)
        if not tab:
            return QVariant()

        if role == self.WebTabRole:
            return QVariant(tab)
        elif role in (self.TitleRole, Qt.DisplayRole):
            return tab.title()
        elif role in (self.IconRole, Qt.DecorationRole):
            return tab.icon()
        elif role == self.PinnedRole:
            return tab.isPinned()
        elif role == self.RestoredRole:
            return tab.isRestored()
        elif role == self.CurrentTabRole:
            return tab.isCurrentTab()
        elif role == self.LoadingRole:
            return tab.isLoading()
        elif role == self.AudioPlayingRole:
            return tab.isPlaying()
        elif role == self.AudioMutedRole:
            return tab.isMuted()
        elif role == self.BackgroundActivityRole:
            return tab.backgroundActivity()
        else:
            return QVariant()

    def supportedDropActions(self):
        '''
        @return: Qt::DropActions
        '''
        return Qt.MoveAction

    def mimeTypes(self):
        '''
        @return: QStringList
        '''
        return [TabModelMimeData.mimeType(), ]

    def mimeData(self, indexes):
        '''
        @param: indexes QModelIndexList
        @return: QMimeData
        '''
        if not indexes:
            return None
        tab = indexes[0].data(self.WebTabRole).value()
        if not tab:
            return None
        mime = TabModelMimeData()
        mime.setTab(tab)
        return mime

    def canDropMimeData(self, data, action, row, column, parent):
        '''
        @param: data QMimeData
        @param: action QDropAction
        @param: row int
        @param: column int
        @param: parent QModelIndex
        '''
        if action != Qt.MoveAction or parent.isValid() or column > 0 or not self._window:
            return False
        mimeData = data  # TODO: qobject_cast<const TabModelMimeData*>
        if not mimeData:
            return False
        return mimeData.tab()

    def dropMimeData(self, data, action, row, column, parent):
        '''
        @param: data QMimeData
        @param: action QDropAction
        @param: row int
        @param: column int
        @param: parent QModelIndex
        '''
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        mimeData = data  # TODO: static_cast<const TabModelMimeData*>
        tab = mimeData.tab()
        if tab.browserWindow() == self._window:
            if row < 0:
                if tab.isPinned():
                    row = self._window.tabWidget().pinnedTabsCount()
                else:
                    row = self._window.tabWidget().count()
            to = row > mimeData.tab().tabIndex() and (row - 1) or row
            tab.moveTab(to)
        else:
            if row < 0:
                row = self._window.tabCount()
            if tab.browserWindow():
                tab.browserWindow().tabWidget().detachTab(tab)
            tab.setPinned(row < self._window.tabWidget().pinnedTabsCount())
            self._window.tabWidget().insertWindow(row, tab, const.NT_SelectedTab)
        return True

    def _init(self):
        for idx in range(self._window.tabCount()):
            self.tabInserted(idx)
        self._window.tabWidget().tabInserted.connect(self.tabInserted)
        self._window.tabWidget().tabRemoved.connect(self.tabRemoved)
        self._window.tabWidget().tabMoved.connect(self.tabMoved)

        def destroyedCb():
            self.beginResetModel()
            self._window = None
            self._tabs.clear()
            self.endResetModel()

        self._window.destroyed.connect(destroyedCb)

    def tabInserted(self, index):
        '''
        @param: index int
        '''
        tab = self._window.tabWidget().webTab(index)
        self.beginInsertRows(QModelIndex(), index, index)
        self._tabs.insert(index, tab)
        self.endInsertRows()

        def emitDataChanged(tab, role):
            idx = self.tabIndex(tab)
            self.dataChanged.emit(idx, idx, [role])

        tab.titleChanged.connect(lambda: emitDataChanged(tab, Qt.DisplayRole))
        tab.titleChanged.connect(lambda: emitDataChanged(tab, self.TitleRole))
        tab.iconChanged.connect(lambda: emitDataChanged(tab, Qt.DecorationRole))
        tab.iconChanged.connect(lambda: emitDataChanged(tab, self.IconRole))
        tab.pinnedChanged.connect(lambda: emitDataChanged(tab, self.PinnedRole))
        tab.restoredChanged.connect(lambda: emitDataChanged(tab, self.RestoredRole))
        tab.currentTabChanged.connect(lambda: emitDataChanged(tab, self.CurrentTabRole))
        tab.loadingChanged.connect(lambda: emitDataChanged(tab, self.LoadingRole))
        tab.playingChanged.connect(lambda: emitDataChanged(tab, self.AudioPlayingRole))
        tab.mutedChanged.connect(lambda: emitDataChanged(tab, self.AudioMutedRole))
        tab.backgroundActivityChanged.connect(lambda: emitDataChanged(tab, self.BackgroundActivityRole))

    def tabRemoved(self, index):
        '''
        @param: index int
        '''
        self.beginRemoveRows(QModelIndex(), index, index)
        self._tabs.pop(index)
        self.endRemoveRows()

    def tabMoved(self, from_, to):
        '''
        @param: from_ int
        @param: to int
        '''
        to1 = to > from_ and to + 1 or to
        if not self.beginMoveRows(QModelIndex(), from_, from_, QModelIndex(), to1):
            print('Invalid beginMoveRows %s %s' % (from_, to1), file=stderr)
        self._tabs.insert(to, self._tabs.pop(from_))
        self.endMoveRows()
