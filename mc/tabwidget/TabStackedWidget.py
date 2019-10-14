from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.Qt import QIcon
from PyQt5.Qt import QTimer
from PyQt5.QtWidgets import QTabBar
from PyQt5.Qt import QEvent
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication

class TabStackedWidget(QWidget):
    '''
    @note: just some of QTabWidget's methods were implemented
    '''
    def __init__(self, parent=None):
        super(TabStackedWidget, self).__init__(parent)
        self._stack = None  # QStackedWidget
        self._tabBar = None  # ComboTabBar
        self._mainLayout = None  # QVBoxLayout
        self._dirtyTabBar = False

        self._currentIndex = 0
        self._previousIndex = 0

        self._stack = QStackedWidget(self)
        self._mainLayout = QVBoxLayout()
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)

        self._mainLayout.addWidget(self._stack)
        self.setLayout(self._mainLayout)

        self._stack.widgetRemoved.connect(self._tabWasRemoved)

    def tabBar(self):
        '''
        @return: ComboTabBar
        '''
        return self._tabBar

    def setTabBar(self, tb):
        '''
        @param: ComboTabBar
        '''
        assert(tb)

        if tb.parentWidget() != self:
            tb.setParent(self)
            tb.show()

        del self._tabBar
        self._dirtyTabBar = True
        self._tabBar = tb
        self.setFocusProxy(self._tabBar)

        self._tabBar.currentChanged.connect(self._showTab)
        self._tabBar.tabMoved.connect(lambda from_, to_: TabStackedWidget._tabWasMoved(self, from_, to_))
        self._tabBar.overFlowChanged.connect(self.setUpLayout)

        if self._tabBar.tabsCloseable():
            self._tabBar.tabCloseRequested.connect(self.tabCloseRequested)

        self.setDocumentMode(self._tabBar.documentMode())

        self._tabBar.installEventFilter(self)
        self.setUpLayout()

    def documentMode(self):
        return self._tabBar.documentMode()

    def setDocumentMode(self, enabled):
        self._tabBar.setDocumentModel(enabled)
        self._tabBar.setExpanding(not enabled)
        self._tabBar.setDrawBase(enabled)

    def addTab(self, widget, label, pinned=False):
        '''
        @return: int
        '''
        return self.insertTab(-1, widget, label, pinned)

    def insertTab(self, index, widget, label, pinned=False):
        '''
        @param: widget QWidget
        @param: label QString
        '''
        if not widget:
            return -1

        if pinned:
            if index < 0:
                index = self._tabBar.pinnedTabsCount()
            else:
                index = min(index, self._tabBar.pinnedTabsCount())
            index = self._stack.insertWidget(index, widget)
            self._tabBar.insertTabByIconText(index, QIcon(), label, True)
        else:
            if index < 0:
                index = self._tabBar.pinnedTabsCount()
            else:
                index = max(index, self._tabBar.pinnedTabsCount())
            index = self._stack.insertWidget(index, widget)
            self._tabBar.insertTabByIconText(index, QIcon(), label, False)

        if self._previousIndex >= index:
            self._previousIndex += 1
        if self._currentIndex >= index:
            self._currentIndex += 1

        QTimer.singleShot(0, self.setUpLayout)

        return index

    def tabText(self, index):
        return self._tabBar.tabText(index)

    def setTabText(self, index, label):
        self._tabBar.setTabText(index, label)

    def tabToolTip(self, index):
        return self._tabBar.tabToolTip(index)

    def setTabToolTip(self, index, tip):
        self._tabBar.setTabToolTip(index, tip)

    def pinUnPinTab(self, index, title=''):
        widget = self._stack.widget(index)
        currentWidget = self._stack.currentWidget()

        if not widget or not currentWidget:
            return -1

        makePinned = index >= self._tabBar.pinnedTabsCount()
        button = self._tabBar.tabButton(index, self._tabBar.iconButtonPosition())
        # To show tooltip of tab which is pinned in the current session
        toolTip = self.tabToolTip(index)

        self._tabBar._blockCurrentChangedSignal = True
        self._tabBar.setTabButton(index, self._tabBar.iconButtonPosition(), None)

        self._stack.removeWidget(widget)
        if makePinned:
            insertIndex = 0
        else:
            insertIndex = self._tabBar.pinnedTabsCount()
        newIndex = self.insertTab(insertIndex, widget, title, makePinned)

        self._tabBar.setTabButton(newIndex, self._tabBar.iconButtonPosition(), button)
        self._tabBar._blockCurrentChangedSignal = False
        self.setTabToolTip(newIndex, toolTip)

        # Restore current widget
        self.setCurrentWidget(currentWidget)

        self.pinStateChanged.emit(newIndex, makePinned)

        return newIndex

    def removeTab(self, index):
        widget = self._stack.widget(index)
        if widget:
            # Select another current tab before remove, so it won't be handled
            # by QTabBar
            if index == self.currentIndex() and self.count() > 1:
                self._selectTabOnRemove()
            self._stack.removeWidget(widget)

    def moveTab(self, from_, to_):
        self._tabBar.moveTab(from_, to_)

    def currentIndex(self):
        '''
        @return: int
        '''
        return self._tabBar.currentIndex()

    def currentWidget(self):
        '''
        @return: QWidget
        '''
        return self._stack.currentWidget()

    def widget(self, index):
        '''
        @return: QWidget
        '''
        return self._stack.widget(index)

    def indexOf(self, widget):
        '''
        @param: widget QWidget
        @return: int
        '''
        return self._stack.indexOf(widget)

    def count(self):
        return self._tabBar.count()

    # Q_SIGNALS
    currentChanged = pyqtSignal(int)  # index
    tabCloseRequested = pyqtSignal(int)  # index
    pinStateChanged = pyqtSignal(int, bool)  # index, pinned

    # public Q_SLOTS
    def setCurrentIndex(self, index):
        self._tabBar.setCurrentIndex(index)

    def setCurrentWidget(self, widget):
        '''
        @widget: widget QWidget
        '''
        self._tabBar.setCurrentIndex(self.indexOf(widget))

    def setUpLayout(self):
        if not self._tabBar.isVisible():
            self._dirtyTabBar = True
            return

        self._tabBar.setElideMode(self._tabBar.elideMode())
        self._dirtyTabBar = False

    # private Q_SLOTS
    def _showTab(self, index):
        if self._validIndex(index):
            self._stack.setCurrentIndex(index)

        self._previousIndex = self._currentIndex
        self._currentIndex = index

        # This is slot connected to ComboTabBar::currentChanged
        # We must send the signal event with invalid index (-1)
        self.currentChanged.emit(index)

    def _tabWasMoved(self, from_, to_):
        self._stack.blockSignals(True)
        widget = self._stack.widget(from_)
        self._stack.removeWidget(widget)
        self._stack.insertWidget(to_, widget)
        self._stack.blockSignals(False)

    def _tabWasRemoved(self, index):
        if self._previousIndex == index:
            self._previousIndex = -1
        elif self._previousIndex > index:
            self._previousIndex -= 1

        if self._currentIndex == index:
            self._currentIndex = -1
        elif self._currentIndex > index:
            self._currentIndex -= 1

        self._tabBar.removeTab(index)

    # protected:
    # override
    def eventFilter(self, obj, event):
        '''
        @param: obj QObject
        @param: event QEvent
        @return: bool
        '''
        if self._dirtyTabBar and obj == self._tabBar and event.type() == QEvent.Show:
            self.setUpLayout()

        return False

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        evkey = event.key()
        evmodifiers = event.modifiers()
        if evkey == Qt.Key_Tab or evkey == Qt.Key_Backtab and \
                self.count() > 1 and evmodifiers & Qt.ControlModifier:
            pageCount = self.count()
            page = self.currentIndex()
            if (evkey == Qt.Key_Backtab) or (evmodifiers & Qt.ShiftModifier):
                dx = -1
            else:
                dx = 1
            for idx in range(pageCount):
                page += dx
                if page < 0:
                    page = self.count() - 1
                elif page >= pageCount:
                    page = 0
                if self._tabBar.isTabEnabled(page):
                    self.setCurrentIndex(page)
                    break
            if not QApplication.focusWidget():
                self._tabBar.setFocus()
        else:
            event.ignore()

    # private:
    def _validIndex(self, index):
        return index < self._stack.count() and index >= 0

    def _selectTabOnRemove(self):
        assert(self.count() > 1)

        index = -1

        behavior = self._tabBar.selectionBehaviorOnRemove()
        if behavior == QTabBar.SelectPreviousTab:
            if self._validIndex(self._previousIndex):
                index = self._previousIndex
            # fallthrough
        elif behavior == QTabBar.SelectLeftTab:
            index = self.currentIndex() - 1
            if not self._validIndex(index):
                index = 1
        elif behavior == QTabBar.SelectRightTab:
            index = self.currentIndex() + 1
            if not self._validIndex(index):
                index = self.currentIndex() - 1

        assert(self._validIndex(index))
        self.setCurrentIndex(index)
