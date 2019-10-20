import peewee
from threading import Lock
from PyQt5.Qt import QAbstractItemModel
from PyQt5.Qt import Qt
from PyQt5.Qt import QSortFilterProxyModel
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QApplication
from PyQt5.Qt import QTimer
from PyQt5.Qt import QIcon
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QDate
from PyQt5.Qt import QTime
from PyQt5.Qt import QModelIndex
from mc.tools.IconProvider import IconProvider
from mc.common.models import HistoryDbModel
from .HistoryItem import HistoryItem

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
        current = QDateTime.currentDateTime()
        if current.date() == dt.date():
            return dt.time().toString('h:mm')

        return dt.toString('yyyy.M.d h:mm')

    def __init__(self, history):
        '''
        @param: history History
        '''
        super().__init__(history)
        self._rootItem = HistoryItem(None)  # HistoryItem
        self._todayItem = None  # HistoryItem
        self._history = history  # History
        self._lock = Lock()

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
            item.delete()
            self.endRemoveRows()

            if item == self._todayItem:
                self._todayItem = None

    # private Q_SLOTS:
    def resetHistory(self):
        self.beginResetModel()

        # TODO: delete m_rootItem
        del self._rootItem
        self._todayItem = None
        self._rootItem = HistoryItem(None)

        self._init()

        self.endResetModel()

    def historyEntryAdded(self, entry):
        '''
        @param: entry HistoryEntry
        '''
        if not self._todayItem:
            self.beginInsertRows(QModelIndex(), 0, 0)

            self._todayItem = HistoryItem(None)
            self._todayItem.canFetchMore = True
            self._todayItem.setStartTimestamp(-1)
            self._todayItem.setEndTimestamp(QDateTime(QDate.currentDate()).toMSecsSinceEpoch())
            self._todayItem.title = _('Today')

            self._rootItem.prependChild(self._todayItem)

            self.endInsertRows()

        self.beginInsertRows(self.createIndex(0, 0, self._todayItem), 0, 0)

        item = HistoryItem()
        item.historyEntry = entry

        self._todayItem.prependChild(item)

        self.endInsertRows()

    def historyEntryDeleted(self, entry):
        '''
        @param: entry HistoryEntry
        '''
        item = self._findHistoryItem(entry)
        if not item:
            return

        parentItem = item.parent()
        row = item.row()

        self.beginRemoveRows(self.createIndex(parentItem.row(), 0, parentItem),
                row, row)
        item.delete()
        self.endRemoveRows()

        self._checkEmptyParentItem(parentItem)

    def historyEntryEdited(self, before, after):
        '''
        @param: before HistoryEntry
        @param: after HistoryEntry
        '''
        with self._lock:
            self.historyEntryDeleted(before)
            self.historyEntryAdded(after)

    # private
    def _findHistoryItem(self, entry):
        '''
        @param: entry HistoryEntry
        @return: HistoryItem
        '''
        # HistoryItem
        parentItem = None
        # qint64
        timestamp = entry.date.toMSecsSinceEpoch()

        for idx in range(self._rootItem.childCount()):
            # HistoryItem
            item = self._rootItem.child(idx)

            if item.endTimestamp() < timestamp:
                parentItem = item
                break

        if not parentItem:
            return None

        for idx in range(parentItem.childCount()):
            item = parentItem.child(idx)
            if item.historyEntry.id == entry.id:
                return item

        return None

    def _checkEmptyParentItem(self, item):
        '''
        @param: item HistoryItem
        '''
        if item.childCount() == 0 and item.isTopLevel():
            row = item.row()

            self.beginRemoveRows(QModelIndex(), row, row)
            item.delete()
            self.endRemoveRows()

            if item == self._todayItem:
                self._todayItem = None

    def _init(self):
        from .History import History
        minTs = HistoryDbModel.select(peewee.fn.Min(HistoryDbModel.date)).scalar()
        if minTs <= 0:
            return

        today = QDate.currentDate()
        week = today.addDays(1 - today.dayOfWeek())
        month = QDate(today.year(), today.month(), 1)
        currentTs = QDateTime.currentMSecsSinceEpoch()

        ts = currentTs
        while ts > minTs:
            tsDate = QDateTime.fromMSecsSinceEpoch(ts).date()
            endTs = 0
            itemName = ''

            if tsDate == today:
                endTs = QDateTime(today).toMSecsSinceEpoch()
                itemName = _('Today')
            elif tsDate >= week:
                endTs = QDateTime(week).toMSecsSinceEpoch()
                itemName = _('This Week')
            elif tsDate.month() == month.month() and tsDate.year() == month.year():
                endTs = QDateTime(month).toMSecsSinceEpoch()
                itemName = _('This Month')
            else:
                startDate = QDate(tsDate.year(), tsDate.month(), tsDate.daysInMonth())
                endDate = QDate(startDate.year(), startDate.month(), 1)

                ts = QDateTime(startDate, QTime(23, 59, 59)).toMSecsSinceEpoch()
                endTs = QDateTime(endDate).toMSecsSinceEpoch()
                itemName = '%s %s' % (tsDate.year(), History.titleCaseLocalizedMonth(tsDate.month()))
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
