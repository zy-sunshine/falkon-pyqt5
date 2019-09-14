from PyQt5.Qt import QIcon
from mc.common.globalvars import gVar

class HistoryItem(object):
    def __init__(self, parent=None):
        '''
        @param: parent HistoryItem
        '''
        from .History import HistoryEntry
        self.historyEntry = HistoryEntry()
        self.title = ''
        self.canFetchMore = False

        self._parent = parent  # HistoryItem
        self._children = []  # QList<HistoryItem>

        self._icon = QIcon()

        self._startTimestamp = 0
        self._endTimestamp = 0

        if self._parent:
            self._parent.appendChild(self)

    def delete(self):
        '''
        @note: same as HistoryItem::~HistoryItem
        '''
        if self._parent:
            self._parent.removeChildByItem(self)

        self._children.clear()

    def changeParent(self, parent):
        '''
        @param: parent HistoryItem
        '''
        if self._parent:
            self._parent.removeChild(self)

        self._parent = parent

        if self._parent:
            self._parent.prependChild(self)

    def parent(self):
        '''
        @return: HistoryItem
        '''
        return self._parent

    def child(self, row):
        '''
        @param: row int
        @return: HistoryItem
        '''
        if gVar.appTools.containsIndex(self._children, row):
            return self._children[row]

        return 0

    def childCount(self):
        '''
        @return: int
        '''
        return len(self._children)

    def prependChild(self, child):
        '''
        @param: child HistoryItem
        '''
        if child in self._children:
            self._children.remove(child)

        child._parent = self
        self._children.insert(0, child)

    def appendChild(self, child):
        '''
        @param: child HistoryItem
        '''
        if child in self._children:
            self._children.remove(child)

        child._parent = self
        self._children.append(child)

    def insertChild(self, row, child):
        '''
        @param: row int
        @param: child HistoryItem
        '''
        if child in self._children:
            self._children.remove(child)

        if len(self._children) >= row:
            child._parent = self
            self._children.insert(row, child)

    def removeChildByRow(self, row):
        '''
        @param: row int
        '''
        if gVar.app.containsIndex(self._children, row):
            self.removeChildByItem(self._children[row])

    def removeChildByItem(self, child):
        '''
        @param: child HistoryItem
        '''
        self._children.remove(child)

    def row(self):
        '''
        @return: int
        '''
        if self._parent:
            return self._parent.indexOfChild(self)
        else:
            return 0

    def indexOfChild(self, child):
        '''
        @param: child HistoryItem
        '''
        return self._children.index(child)

    def isTopLevel(self):
        '''
        @return: bool
        '''
        return self._startTimestamp != 0

    def icon(self):
        '''
        @return: QIcon
        '''
        return self._icon

    def setIcon(self, icon):
        '''
        @param: icon QIcon
        '''
        self._icon = icon

    def setStartTimestamp(self, start):
        '''
        @param: start qint64
        '''
        self._startTimestamp = start

    def startTimestamp(self):
        '''
        @param: qint64
        '''
        return self._startTimestamp

    def setEndTimestamp(self, end):
        '''
        @param: end qint64
        '''
        self._endTimestamp = end

    def endTimestamp(self):
        '''
        @return: qint64
        '''
        return self._endTimestamp
