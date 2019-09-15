from PyQt5.QtWidgets import QTreeWidget
from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItem

class TreeWidget(QTreeWidget):
    # enum ItemShowMode
    ItemsCollapsed = 0
    ItemsExpanded = 1
    def __init__(self, parent=None):
        super().__init__(parent)
        self._refreshAllItemsNeeded = True
        self._allTreeItems = []  # QList<QTreeWidgetItem>
        self._showMode = 0  # ItemShowMode

    def defaultItemShowMode(self):
        '''
        @return: ItemShowMode
        '''
        return self._showMode

    def setDefaultItemShowModel(self, mode):
        '''
        @param: item ItemShowMode
        '''
        self._showMode = mode

    def allItems(self):
        '''
        @return: QList<QTreeWidgetItem>
        '''
        pass

    def appendToParentItemByText(self, parentText, item):
        '''
        @param: parentText QString
        @param: item QTreeWidgetItem
        '''
        pass

    def appendToParentItemByItem(self, parent, item):
        pass

    def prependToParentItemByText(self, parentText, item):
        pass

    def prependToParentItemByItem(self, parent, item):
        pass

    def addTopLevelItem(self, item):
        '''
        @param: item QTreeWidgetItem
        '''
        pass

    def addTopLevelItems(self, items):
        '''
        @param: items QList<QTreeWidgetItem>
        '''
        pass

    def insertTopLevelItem(self, index, item):
        '''
        @param: index int
        @param: item QTreeWidgetItem
        '''
        pass

    def insertTopLevelItems(self, index, items):
        '''
        @param: index int
        @param: items QList<QTreeWidgetItem>
        '''

    def deleteItem(self, item):
        '''
        @param: item QTreeWidgetItem
        '''
        pass

    def deleteItems(self, items):
        '''
        @param: items QList<QTreeWidgetItem>
        '''
        pass

    # Q_SIGNALS:
    itemControlClicked = pyqtSignal(QTreeWidgetItem)  # item
    itemMiddleButtonClicked = pyqtSignal(QTreeWidgetItem)  # item

    # public Q_SLOTS:
    def filterString(self, string):
        pass

    def clear(self):
        pass

    # private Q_SLOTS:
    def _scheduleRefresh(self):
        pass

    # private:
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    def iterateAllItems(self, parent):
        '''
        @param: parent QTreeWidgetItem
        '''
        pass
