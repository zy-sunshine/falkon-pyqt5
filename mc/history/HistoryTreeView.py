from PyQt5.QtWidgets import QTreeView
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QPoint
from PyQt5.Qt import QUrl

class HistoryTreeView(QTreeView):
    # enum TreeView
    HistoryManagerViewType = 0
    HistorySidebarViewType = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = None  # History
        self._filter = None  # HistoryFilterModel
        self._header = None  # HeaderView
        self._type = self.HistoryManagerViewType  # ViewType

    def viewType(self):
        return self._type

    def setViewType(self, type_):
        self._type = type_

    def selectedUrl(self):
        '''
        @brief: Returns empty urls if more than one (or zero) urls are selected
        @return: QUrl
        '''
        pass

    def header(self):
        '''
        @return: HeaderView
        '''
        pass

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
        pass

    def removeSelectedItems(self):
        pass

    # protected:
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

    # override
    def drawRow(self, painter, options, index):
        '''
        @param: painter QPainter
        @param: options QStyleOptionViewItem
        @param: index QModelIndex
        '''
        pass
