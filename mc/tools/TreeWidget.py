from PyQt5.QtWidgets import QTreeWidget
from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.Qt import Qt

class TreeWidget(QTreeWidget):
    # enum ItemShowMode
    ItemsCollapsed = 0
    ItemsExpanded = 1
    def __init__(self, parent=None):
        super().__init__(parent)
        self._refreshAllItemsNeeded = True
        self._allTreeItems = []  # QList<QTreeWidgetItem>
        self._showMode = self.itemCollapsed  # ItemShowMode

        self.itemChanged.connect(self._scheduleRefresh)

    def defaultItemShowMode(self):
        '''
        @return: ItemShowMode
        '''
        return self._showMode

    def setDefaultItemShowMode(self, mode):
        '''
        @param: item ItemShowMode
        '''
        self._showMode = mode

    def allItems(self):
        '''
        @return: QList<QTreeWidgetItem>
        '''
        if self._refreshAllItemsNeeded:
            self._allTreeItems.clear()
            self.iterateAllItems(None)
            self._refreshAllItemsNeeded = False

        return self._allTreeItems

    def appendToParentItemByText(self, parentText, item):
        '''
        @param: parentText QString
        @param: item QTreeWidgetItem
        '''
        list_ = self.findItems(parentText, Qt.MatchExactly)
        if len(list_) == 0:
            return False
        # QTreeWidgetItem
        parentItem = list_[0]
        if not parentItem:
            return False

        self._allTreeItems.append(item)
        parentItem.addChild(item)
        return True

    def appendToParentItemByItem(self, parent, item):
        if not parent or parent.treeWidget() != self:
            return False

        self._allTreeItems.append(item)
        parent.appendChild(item)
        return True

    def prependToParentItemByText(self, parentText, item):
        list_ = self.findItems(parentText, Qt.MatchExactly)
        if len(list_) == 0:
            return False
        # QTreeWidgetItem
        parentItem = list_[0]
        if not parentItem:
            return False

        self._allTreeItems.append(item)
        parentItem.insertChild(0, item)
        return True

    def prependToParentItemByItem(self, parent, item):
        if not parent or parent.treeWidget() != self:
            return False

        self._allTreeItems.append(item)
        parent.insertChild(0, item)
        return True

    def addTopLevelItem(self, item):
        '''
        @param: item QTreeWidgetItem
        '''
        self._allTreeItems.append(item)
        super().addTopLevelItem(item)

    def addTopLevelItems(self, items):
        '''
        @param: items QList<QTreeWidgetItem>
        '''
        self._allTreeItems.extend(items)
        super().addTopLevelItems(items)

    def insertTopLevelItem(self, index, item):
        '''
        @param: index int
        @param: item QTreeWidgetItem
        '''
        self._allTreeItems.append(item)
        super().insertTopLevelItem(index, item)

    def insertTopLevelItems(self, index, items):
        '''
        @param: index int
        @param: items QList<QTreeWidgetItem>
        '''
        self._allTreeItems.extend(items)
        super().insertTopLevelItems(index, items)

    def deleteItem(self, item):
        '''
        @param: item QTreeWidgetItem
        '''
        if item in self._allTreeItems:
            self._allTreeItems.remove(item)

        self._refreshAllItemsNeeded = True

    def deleteItems(self, items):
        '''
        @param: items QList<QTreeWidgetItem>
        '''
        for item in items:
            if item in self._allTreeItems:
                self._allTreeItems.remove(item)

        self._refreshAllItemsNeeded = True

    # Q_SIGNALS:
    itemControlClicked = pyqtSignal(QTreeWidgetItem)  # item
    itemMiddleButtonClicked = pyqtSignal(QTreeWidgetItem)  # item

    # public Q_SLOTS:
    def filterString(self, string):
        # QList<QTreeWidgetItem>
        _allItems = self.allItems()
        # QList<QTreeWidgetItem>
        parents = []
        stringIsEmpty = not string
        strLower = string.lower()
        for item in _allItems:
            if stringIsEmpty:
                containsString = True
            else:
                text = item.text(0).lower()
                containsString = strLower in text
            if containsString:
                item.setHidden(False)
                itemParent = item.parent()
                if itemParent and itemParent not in parents:
                    parents.append(itemParent)
            else:
                item.setHidden(True)
                itemParent = item.parent()
                if itemParent:
                    itemParent.setHidden(True)

        for parentItem in parents:
            parentItem.setHidden(False)
            if stringIsEmpty:
                parentItem.setExpanded(self._showMode == self.itemExpanded)
            else:
                parentItem.setExpanded(True)

            parentOfParentItem = parentItem.parent()
            if parentOfParentItem and parentOfParentItem not in parents:
                parents.append(parentOfParentItem)

    def clear(self):
        super().clear()
        self._allTreeItems.clear()

    # private Q_SLOTS:
    def _scheduleRefresh(self):
        self._refreshAllItemsNeeded = True

    # private:
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if event.modifiers() == Qt.ControlModifier:
            self.itemControlClicked.emit(self.itemAt(event.pos()))

        if event.buttons() == Qt.MiddleButton:
            self.itemMiddleButtonClicked.emit(self.itemAt(event.pos()))

        super().mousePressEvent(event)

    def iterateAllItems(self, parent):
        '''
        @param: parent QTreeWidgetItem
        '''
        if parent:
            count = parent.childCount()
        else:
            count = self.topLevelItemCount()

        for idx in range(count):
            if parent:
                item = parent.child(idx)
            else:
                item = self.topLevelItem(idx)

            if item.childCount() == 0:
                self._allTreeItems.append(item)

            self.iterateAllItems(item)
