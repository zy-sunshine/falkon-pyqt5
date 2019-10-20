from PyQt5.QtWidgets import QTreeView
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QPoint
from PyQt5.Qt import QUrl
from PyQt5.QtWidgets import QAbstractItemView
from .HistoryModel import HistoryModel
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import Qt
from mc.common.globalvars import gVar
from .HistoryModel import HistoryFilterModel
from mc.tools.HeaderView import HeaderView
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QPersistentModelIndex

class HistoryTreeView(QTreeView):
    # enum TreeView
    HistoryManagerViewType = 0
    HistorySidebarViewType = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = gVar.app.history()  # History
        self._filter = HistoryFilterModel(self._history.model())  # HistoryFilterModel
        self._header = None  # HeaderView
        self._type = self.HistoryManagerViewType  # ViewType

        self.setModel(self._filter)

        self.setUniformRowHeights(True)
        self.setAllColumnsShowFocus(True)

        self._header = HeaderView(self)
        self._header.setDefaultSelectionSizes([0.4, 0.35, 0.10, 0.08])
        self._header.setSectionHidden(4, True)
        self.setHeader(self._header)

        self._filter.expandAllItems.connect(self.expandAll)
        self._filter.collapseAllItems.connect(self.collapseAll)

    def viewType(self):
        return self._type

    def setViewType(self, type_):
        self._type = type_

        if type_ == self.HistoryManagerViewType:
            self.setColumnHidden(1, False)
            self.setColumnHidden(2, False)
            self.setColumnHidden(3, False)
            self.setHeaderHidden(False)
            self.setMouseTracking(False)
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        elif type_ == self.HistorySidebarViewType:
            self.setColumnHidden(1, True)
            self.setColumnHidden(2, True)
            self.setColumnHidden(3, True)
            self.setHeaderHidden(True)
            self.setMouseTracking(True)
            self.setSelectionMode(QAbstractItemView.SingleSelection)

    def selectedUrl(self):
        '''
        @brief: Returns empty urls if more than one (or zero) urls are selected
        @return: QUrl
        '''
        # QList<QModelIndex>
        indexes = self.selectionModel().selectedRows()

        if len(indexes) != 1:
            return QUrl()

        # TopLevelItems have invalid (empty) UrlRole data
        result = indexes[0].data(HistoryModel.UrlRole)
        if not result:
            result = QUrl()
        return result

    def header(self):
        '''
        @return: HeaderView
        '''
        return self._header

    # Q_SIGNALS:
    # Open url in current tab
    urlActivated = pyqtSignal(QUrl)  # item
    # Open url in new tab
    urlCtrlActivated = pyqtSignal(QUrl)  # item
    # Open url in new window
    urlShiftActivated = pyqtSignal(QUrl)  # item
    # Context menu signal with point mapped to global
    contextMenuRequested = pyqtSignal(QPoint)  # point

    # public Q_SLOTS:
    def search(self, string):
        '''
        @param: string QString
        '''
        self._filter.setFilterFixedString(string)

    def removeSelectedItems(self):
        list_ = []  # QList<int>
        QApplication.setOverrideCursor(Qt.WaitCursor)

        topLevelIndexes = []  # QList<QPersistentModelIndex>

        for index in self.selectedIndexes():
            if index.column() > 0:
                continue

            if index.data(HistoryModel.IsTopLevelRole):
                start = index.data(HistoryModel.TimestampStartRole)
                end = index.data(HistoryModel.TimestampEndRole)

                list_.append(self._history.indexesFromTimeRange(start, end))

                topLevelIndexes.append(index)
            else:
                id_ = index.data(HistoryModel.IdRole)
                if id_ not in list_:
                    list_.append(id_)

        self._history.deleteHistoryEntry(list_)
        self._history.model().removeTopLevelIndexes(topLevelIndexes)

        QApplication.restoreOverrideCursor()

    # protected:
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
        super().mouseMoveEvent(event)

        if self._type == self.HistorySidebarViewType:
            # QCursor
            cursor = Qt.ArrowCursor
            if event.buttons() == Qt.NoButton:
                # QModelIndex
                index = self.indexAt(event.pos())
                if index.isValid() and not index.data(HistoryModel.IsTopLevelRole):
                    cursor = Qt.PointingHandCursor
            self.viewport().setCursor(cursor)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mousePressEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            index = self.indexAt(event.pos())
            # Qt::MouseButtons
            buttons = event.buttons()
            # Qt::KeyboardModifiers
            modifiers = event.modifiers()

            if index.isValid() and not index.data(HistoryModel.IsTopLevelRole):
                # QUrl
                url = index.data(HistoryModel.UrlRole)  # toUrl()

                if buttons == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                    self.urlShiftActivated.emit(url)
                elif buttons == Qt.MiddleButton or (buttons == Qt.LeftButton and
                        modifiers == Qt.ControlModifier):
                    self.urlCtrlActivated.emit(url)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mouseReleaseEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            index = self.indexAt(event.pos())

            if index.isValid() and not index.data(HistoryModel.IsTopLevelRole):
                url = index.data(HistoryModel.UrlRole)  # toUrl()

                # Activate urls with single mouse click in SideBar
                if self._type == self.HistorySidebarViewType and event.button() == \
                        Qt.LeftButton and event.modifiers() == Qt.NoModifier:
                    self.urlActivated.emit(url)

    # override
    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mouseDoubleClickEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            index = self.indexAt(event.pos())

            if index.isValid() and not index.data(HistoryModel.IsTopLevelRole):
                url = index.data(HistoryModel.UrlRole)  # toUrl()
                buttons = event.buttons()
                modifiers = event.modifiers()

                if buttons == Qt.LeftButton and modifiers == Qt.NoModifier:
                    self.urlActivated.emit(url)
                elif buttons == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                    self.urlShiftActivated.emit(url)

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        super().keyPressEvent(event)

        if len(self.selectionModel().selectedRows()) == 1:
            index = self.selectionModel().selectedRows()[0]
            url = index.data(HistoryModel.UrlRole)  # toUrl()
            isTopLevel = index.data(HistoryModel.IsTopLevelRole)  # toBool()
            modifiers = event.modifiers()

            evtKey = event.key()
            if evtKey in (Qt.Key_Return, Qt.Key_Enter):
                if isTopLevel and modifiers in (Qt.NoModifier, Qt.KeypadModifier):
                    self.setExpanded(index, not self.isExpanded(index))
                else:
                    if modifiers in (Qt.NoModifier, Qt.KeypadModifier):
                        self.urlActivated.emit(url)
                    elif modifiers == Qt.ControlModifier:
                        self.urlCtrlActivated.emit(url)
                    elif modifiers == Qt.ShiftModifier:
                        self.urlShiftActivated.emit(url)
            elif evtKey == Qt.Key_Delete:
                self.removeSelectedItems()

    # override
    def drawRow(self, painter, options, index):
        '''
        @param: painter QPainter
        @param: options QStyleOptionViewItem
        @param: index QModelIndex
        '''
        itemTopLevel = index.data(HistoryModel.IsTopLevelRole)  # toBool()
        icon = index.data(HistoryModel.IconRole)
        iconLoaded = icon and not icon.isNull()

        if index.isValid() and not itemTopLevel and not iconLoaded:
            # QPersistentModelIndex
            _ = QPersistentModelIndex(index)
            url = index.data(HistoryModel.UrlRole)  # toUrl()
            self.model().setData(index, IconProvider.iconForUrl(url), HistoryModel.IconRole)

        super().drawRow(painter, options, index)
