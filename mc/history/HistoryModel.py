import peewee
from PyQt5.Qt import QAbstractItemModel
from PyQt5.Qt import Qt
from .HistoryItem import HistoryItem
from PyQt5.Qt import QSortFilterProxyModel
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QApplication
from PyQt5.Qt import QTimer
from PyQt5.Qt import QIcon
from datetime import datetime
from datetime import timedelta
from datetime import time as dttime
from PyQt5.Qt import QModelIndex
from mc.tools.IconProvider import IconProvider
from mc.common.models import HistoryDbModel

class HistoryModel(QAbstractItemModel):
    # enum Roles
    IdRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    UrlRole = Qt.UserRole + 3
    UrlStringRole = Qt.UserRole + 4
    IconRole = Qt.UserRole + 5
    IsTopLevelRole = Qt.UserRole + 7
    TimestampStartRole = Qt.UserRole + 8
    TimestampEndRole = Qt.UserRole + 9
    MaxRole = TimestampEndRole

    @classmethod
    def _s_dateTimeToString(cls, dt):
        current = datetime.now()
        if current.date() == dt.date():
            return dt.strftime('%H:%M')

        return dt.strftime('%Y-%d-%m %H:%M')

    def __init__(self, history):
        '''
        @param: history History
        '''
        super().__init__(history)
        self._rootItem = HistoryItem(None)  # HistoryItem
        self._todayItem = None  # HistoryItem
        self._history = history  # History

        self._init()

        self._history.resetHistory.connect(self.resetHistory)
        self._history.historyEntryAdded.connect(self.historyEntryAdded)
        self._history.historyEntryDeleted.connect(self.historyEntryDeleted)
        self._history.historyEntryEdited.connect(self.historyEntryEdited)

    # override
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''
        @param: section
        @param: orientation Qt.Orientation
        @return: QVariant
        '''
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return _('Title')
            elif section == 1:
                return _('Address')
            elif section == 2:
                return _('Visit Date')
            elif section == 3:
                return _('Visit Count')

        return super().headerData(section, orientation, role)

    # override
    def data(self, index, role):  # noqa C901
        '''
        @param: index QModelIndex
        @param: role int
        @return: Qvariant
        @critical: donot return '' empty string for null case, that will cause
            QTreeView row not draw, return None instead (Qt return QVariant())
        '''
        # HistoryItem
        item = self.itemFromIndex(index)

        if index.row() < 0 or not item:
            return None

        if item.isTopLevel():
            if role == self.IsTopLevelRole:
                return True
            elif role == self.TimestampStartRole:
                return item.startTimestamp()
            elif role == self.TimestampEndRole:
                return item.endTimestamp()
            elif role in (Qt.DisplayRole, Qt.EditRole):
                if index.column() == 0:
                    return item.title
                else:
                    return None
            elif role == Qt.DecorationRole:
                if index.column() == 0:
                    return QIcon.fromTheme('view-calendar', QIcon(':/icons/menu/history_entry.svg'))
                else:
                    return None

            return None

        entry = item.historyEntry

        if role == self.IdRole:
            return entry.id
        elif role == self.TitleRole:
            return entry.title
        elif role == self.UrlRole:
            return entry.url
        elif role == self.UrlStringRole:
            return entry.urlString
        elif role == self.IconRole:
            return item.icon()
        elif role == self.IsTopLevelRole:
            return False
        elif role == self.TimestampStartRole:
            return -1
        elif role == self.TimestampEndRole:
            return -1
        elif role in (Qt.ToolTipRole, Qt.DisplayRole, Qt.EditRole):
            if role == Qt.ToolTipRole:
                if index.column() == 0:
                    return '%s\n%s' % (entry.title, entry.urlString)
            # fallthrough
            column = index.column()
            if column == 0:
                return entry.title
            elif column == 1:
                return entry.urlString
            elif column == 2:
                return self._s_dateTimeToString(entry.date)
            elif column == 3:
                return entry.count
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                if item.icon().isNull():
                    return IconProvider.emptyWebIcon()
                else:
                    return item.icon()

        return None

    # override
    def setData(self, index, value, role):
        '''
        @param: index QModelIndex
        @param: value QVariant
        @param: role int
        '''
        # HistoryItem
        item = self.itemFromIndex(index)

        if item.row() < 0 or not item or item.isTopLevel():
            return False

        if role == self.IconRole:
            assert(isinstance(value, QIcon))
            item.setIcon(value)
            self.dataChanged.emit(index, index)
            return True

        return False

    # override
    def index(self, row, column, parent=QModelIndex()):
        '''
        @param: row int
        @param: column int
        @param: parent
        '''
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem = self.itemFromIndex(parent)
        childItem = parentItem.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    # override
    def parent(self, child):
        '''
        @param: child QModelIndex
        '''
        if not child.isValid():
            return QModelIndex()

        childItem = self.itemFromIndex(child)
        parentItem = childItem.parent()

        if not parentItem or parentItem == self._rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    # override
    def flags(self, index):
        '''
        @param: index QModelIndex
        @return: Qt.ItemFlags
        '''
        if not index.isValid():
            return 0

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # override
    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        parentItem = self.itemFromIndex(parent)

        return parentItem.childCount()

    # override
    def columnCount(self, parent=QModelIndex()):
        return 4

    # override
    def canFetchMore(self, parent):
        '''
        @param: parent QModelIndex
        '''
        parentItem = self.itemFromIndex(parent)

        if parentItem:
            return parentItem.canFetchMore
        else:
            return False

    # override
    def fetchMore(self, parent):
        '''
        @param: parent QModelIndex
        '''
        from .History import HistoryEntry
        parentItem = self.itemFromIndex(parent)

        if not parent.isValid() or not parentItem:
            return

        parentItem.canFetchMore = False
        idList = []  # QList<int>
        for idx in range(parentItem.childCount()):
            idList.append(parentItem.child(idx).historyEntry.id)

        list_ = []  # QVector<HistoryEntry>
        dbobjs = HistoryDbModel.select().where(HistoryDbModel.date.between(
            parentItem.endTimestamp(), parentItem.startTimestamp()))
        for dbobj in dbobjs:
            entry = HistoryEntry.CreateFromDbobj(dbobj)
            if entry.id not in idList:
                list_.append(entry)

        if not list_:
            return

        # TODO: prepend or append for new row positions?
        self.beginInsertRows(parent, 0, len(list_) - 1)

        for entry in list_:
            newItem = HistoryItem(parentItem)
            newItem.historyEntry = entry

        self.endInsertRows()

    # override
    def hasChildren(self, parent):
        '''
        @param: parent QModelIndex
        '''
        if not parent.isValid():
            return True

        item = self.itemFromIndex(parent)

        if item:
            return item.isTopLevel()
        else:
            return False

    def itemFromIndex(self, index):
        '''
        @param: index QModelIndex
        @return: HistoryItem
        '''
        if index.isValid():
            # HistoryItem* item = static_cast<HistoryItem*>(index.internalPointer());
            item = index.internalPointer()
            if isinstance(item, HistoryItem):
                return item

        return self._rootItem

    def removeTopLevelIndexes(self, indexes):
        '''
        @param: indexes QList<QPersistentModelIndex>
        '''
        for index in indexes:
            if index.parent().isValid():
                continue

            row = index.row()
            item = self._rootItem.child(row)

            if not item:
                return

            self.beginRemoveRows(QModelIndex(), row, row)
            # TODO: delete item
            self.removeRow(item)
            self.endRemoveRows()

            if item == self._todayItem:
                self._todayItem = None

    # private Q_SLOTS:
    def resetHistory(self):
        self.beginResetModel()

        # TODO: delete m_rootItem
        del self._rootItem
        self._todayItem = None
        self._rootItem = HistoryItem(0)

        self._init()

        self.endResetModel()

    def historyEntryAdded(self, entry):
        '''
        @param: entry HistoryEntry
        '''
        pass

    def historyEntryDeleted(self, entry):
        '''
        @param: entry HistoryEntry
        '''
        pass

    def historyEntryEdited(self, before, after):
        '''
        @param: before HistoryEntry
        @param: after HistoryEntry
        '''
        pass

    # private
    def _findHistoryItem(self, entry):
        '''
        @param: entry HistoryEntry
        @return: HistoryItem
        '''
        pass

    def _checkEmptyParentItem(self, item):
        '''
        @param: item HistoryItem
        '''
        pass

    def _init(self):
        from .History import History
        minTs = HistoryDbModel.select(peewee.fn.Min(HistoryDbModel.date)).scalar()
        if minTs <= 0:
            return

        today = datetime.now()
        currentTs = int(today.timestamp())
        todayDate = today.date()
        today = datetime.combine(todayDate, dttime(0, 0, 0))
        week = today - timedelta(days=today.weekday())
        month = datetime(today.year, today.month, 1)
        monthDate = month.date()

        weekDate = week.date()

        ts = currentTs
        while ts > minTs:
            tsDate = datetime.fromtimestamp(ts).date()
            endTs = 0
            itemName = ''

            if tsDate == todayDate:
                endTs = int(today.timestamp())
                itemName = _('Today')
            elif tsDate >= weekDate:
                endTs = int(week.timestamp())
                itemName = _('This Week')
            elif tsDate.month == monthDate.month and tsDate.year == monthDate.year:
                endTs = int(month.timestamp())
                itemName = _('This Month')
            else:
                startDate = datetime.date(tsDate.year, tsDate.month, tsDate.day)
                endDate = datetime.date(startDate.year, startDate.month, 1)

                ts = datetime.combine(startDate, dttime(23, 59, 59)).timestamp()
                ts = int(ts)
                endTs = datetime.combine(endDate, dttime(0, 0, 0)).timestamp()
                endTs = int(endTs)
                itemName = '%s %s' % (tsDate.year, History.titleCaseLocalizedMonth(tsDate.month))
            dbobj = HistoryDbModel.select().where(HistoryDbModel.date.between(endTs, ts)).first()
            if dbobj:
                item = HistoryItem(self._rootItem)
                item.setStartTimestamp(ts == currentTs and -1 or ts)
                item.setEndTimestamp(endTs)
                item.title = itemName
                item.canFetchMore = True

                if ts == currentTs:
                    self._todayItem = item

            ts = endTs - 1

class HistoryFilterModel(QSortFilterProxyModel):
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

    # public Q_SLOTS
    def setFilterFixedString(self, pattern):
        '''
        @param: pattern QString
        '''
        self._pattern = pattern

        self._filterTimer.start()

    # Q_SIGNALS
    expandAllItems = pyqtSignal()
    collapseAllItems = pyqtSignal()

    # protected:
    # override
    def filterAcceptsRow(self, sourceRow, sourceParent):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        isTopLevel = index.data(HistoryModel.IsTopLevelRole)
        if isTopLevel:
            return True

        urlString = index.data(HistoryModel.UrlStringRole).lower()
        title = index.data(HistoryModel.TitleRole).lower()
        return self._pattern.lower() in urlString or self._pattern.lower() in title

    # private Q_SLOTS:
    def _startFiltering(self):
        if not self._pattern:
            self.collapseAllItems.emit()
            super().setFilterFixedString(self._pattern)
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        # Expand all items also calls fetchmore
        self.expandAllItems.emit()

        super().setFilterFixedString(self._pattern)

        QApplication.restoreOverrideCursor()
