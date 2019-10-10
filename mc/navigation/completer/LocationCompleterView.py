from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QModelIndex
from PyQt5.Qt import Qt
from PyQt5.Qt import QVBoxLayout, QHBoxLayout
from PyQt5.Qt import QFrame
from PyQt5.Qt import QSize
from PyQt5.Qt import QTimer
from PyQt5.Qt import QEvent
from PyQt5.Qt import QKeyEvent
from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QListView
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QLabel
from mc.webengine.LoadRequest import LoadRequest
from mc.common import const
from mc.common.globalvars import gVar
from mc.tools.ToolButton import ToolButton
from mc.tools.IconProvider import IconProvider
from .LocationCompleterDelegate import LocationCompleterDelegate
from .LocationCompleterModel import LocationCompleterModel

class LocationCompleterView(QWidget):
    def __init__(self):
        super().__init__(None)
        self._view = None  # QListView
        self._delegate = None  # LocationCompleterDelegate
        self._searchEnginesLayout = None  # QHBoxLayout
        self._resizeHeight = -1
        self._resizeTimer = None  # QTimer
        self._forceResize = True

        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeCombo)

        if gVar.app.platformName() == 'xcb':
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint |
                    Qt.BypassWindowManagerHint)
        else:
            self.setWindowFlags(Qt.Popup)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._view = QListView(self)
        layout.addWidget(self._view)

        self._view.setUniformItemSizes(True)
        self._view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._view.setSelectionMode(QAbstractItemView.SingleSelection)

        self._view.setMouseTracking(True)
        gVar.app.installEventFilter(self)

        self._delegate = LocationCompleterDelegate(self)
        # TODO:
        #self._view.setItemDelegate(self._delegate)

        searchFrame = QFrame(self)
        searchFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        searchLayout = QHBoxLayout(searchFrame)
        searchLayout.setContentsMargins(10, 4, 4, 4)

        searchSettingsButton = ToolButton(self)
        searchSettingsButton.setIcon(IconProvider.settingsIcon())
        searchSettingsButton.setToolTip(_('Manage Search Engines'))
        searchSettingsButton.setAutoRaise(True)
        searchSettingsButton.setIconSize(QSize(16, 16))
        searchSettingsButton.clicked.connect(self.searchEnginesDialogRequested)

        searchLabel = QLabel(_('Search with:'))
        self._searchEnginesLayout = QHBoxLayout()

        self._setupSearchEngines()
        gVar.app.searchEnginesManager().enginesChanged.connect(self._setupSearchEngines)

        searchLayout.addWidget(searchLabel)
        searchLayout.addLayout(self._searchEnginesLayout)
        searchLayout.addStretch()
        searchLayout.addWidget(searchSettingsButton)

        layout.addWidget(searchFrame)

    def model(self):
        '''
        @return: QAbstractItemModel
        '''
        return self._view.model()

    def setModel(self, model):
        '''
        @param model QAbstractItemModel
        '''
        self._view.setModel(model)

    def selectionModel(self):
        '''
        @return: QItemSelectionModel
        '''
        return self._view.selectionModel()

    def currentIndex(self):
        '''
        @return: QModelIndex
        '''
        return self._view.currentIndex()

    def setCurrentIndex(self, index):
        '''
        @param index QModelIndex
        '''
        self._view.setCurrentIndex(index)

    def adjustSize(self):
        maxItemsCount = 12
        newHeight = self._view.sizeHintForRow(0) * min(maxItemsCount, self.model().rowCount())

        if not self._resizeTimer:
            self._resizeTimer = QTimer(self)
            self._resizeTimer.setInterval(200)

            def func():
                if self._resizeHeight > 0:
                    self._view.setFixedHeight(self._resizeHeight)
                    self.setFixedHeight(self.sizeHint().height())
                self._resizeHeight = -1
            self._resizeTimer.timeout.connect(func)

        if not self._forceResize:
            if newHeight == self._resizeHeight:
                return
            elif newHeight == self._view.height():
                self._resizeHeight = -1
                return
            elif newHeight < self._view.height():
                self._resizeHeight = newHeight
                self._resizeTimer.start()
                return

        self._resizeHeight = -1
        self._forceResize = False
        self._view.setFixedHeight(newHeight)
        self.setFixedHeight(self.sizeHint().height())

    # override
    def eventFilter(self, obj, event):  # noqa C901
        '''
        @param obj QObject
        @param event QEvent
        @return: bool
        '''
        # Event filter based on QCompleter::eventFilter from qcompleter.cpp
        if obj == self or obj == self._view or not self.isVisible():
            return False

        evtType = event.type()
        if obj == self._view.viewport():
            if evtType == QEvent.MouseButtonRelease:
                # QMouseEvent
                e = event
                index = self._view.indexAt(e.pos())
                if not index.isValid():
                    return False

                # Qt::MouseButton
                button = e.button()
                # Qt::KeyboardModifiers
                modifiers = e.modifiers()

                if button == Qt.LeftButton and modifiers == Qt.NoModifier:
                    self.indexActivated.emit(index)
                    return True

                if button == Qt.MiddleButton or (button == Qt.LeftButton and modifiers == Qt.ControlModifier):
                    self.indexCtrlActivated.emit(index)
                    return True

                if button == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                    self.indexShiftActivated.emit(index)
                    return True

            return False

        if evtType == QEvent.KeyPress:
            # QKeyEvent
            keyEvent = event
            evtKey = keyEvent.key()
            modifiers = keyEvent.modifiers()
            index = self._view.currentIndex()
            item = self.model().index(0, 0)
            if item.data(LocationCompleterModel.VisitSearchItemRole):
                visitSearchIndex = item
            else:
                visitSearchIndex = QModelIndex()

            if (evtKey == Qt.Key_Up or evtKey == Qt.Key_Down) and \
                    self._view.currentIndex() != index:
                self._view.setCurrentIndex(index)  # TODO: ?

            if evtKey in (Qt.Key_Return, Qt.Key_Enter):
                if index.isValid():
                    if modifiers == Qt.NoModifier or modifiers == Qt.KeypadModifier:
                        self.indexActivated.emit(index)
                        return True

                    if modifiers == Qt.ControlModifier:
                        self.indexCtrlActivated.emit(index)
                        return True

                    if modifiers == Qt.ShiftModifier:
                        self.indexShiftActivated.emit(index)
                        return True

            elif evtKey == Qt.Key_End:
                if modifiers & Qt.ControlModifier:
                    self._view.setCurrentIndex(
                        self.model().index(self.model().rowCount() - 1, 0)
                    )
                    return True
                else:
                    self.close()

            elif evtKey == Qt.Key_Home:
                if modifiers & Qt.ControlModifier:
                    self._view.setCurrentIndex(self.model().index(0, 0))
                    self._view.scrollToTop()
                    return True
                else:
                    self.close()

            elif evtKey == Qt.Key_Escape:
                self.close()
                return True

            elif evtKey == Qt.Key_F4:
                if modifiers == Qt.AltModifier:
                    self.close()
                    return False

            elif evtKey in (Qt.Key_Tab, Qt.Key_Backtab):
                if modifiers != Qt.NoModifier and modifiers != Qt.ShiftModifier:
                    return False
                isBack = evtKey == Qt.Key_Backtab
                if evtKey == Qt.Key_Tab and modifiers == Qt.ShiftModifier:
                    isBack = True
                ev = QKeyEvent(QKeyEvent.KeyPress, isBack and Qt.Key_Up or Qt.Key_Down,
                        Qt.NoModifier)
                QApplication.sendEvent(self.focusProxy(), ev)
                return True

            elif evtKey in (Qt.Key_Up, Qt.Key_PageUp):
                if modifiers != Qt.NoModifier:
                    return False
                step = evtKey == Qt.Key_PageUp and 5 or 1
                if not index.isValid() or index == visitSearchIndex:
                    rowCount = self.model().rowCount()
                    lastIndex = self.model().index(rowCount - 1, 0)
                    self._view.setCurrentIndex(lastIndex)
                elif index.row() == 0:
                    self._view.setCurrentIndex(QModelIndex())
                else:
                    row = max(0, index.row() - step)
                    self._view.setCurrentIndex(self.model().index(row, 0))
                return True

            elif evtKey in (Qt.Key_Down, Qt.Key_PageDown):
                if modifiers != Qt.NoModifier:
                    return False
                step = evtKey == Qt.Key_PageDown and 5 or 1
                if not index.isValid():
                    firstIndex = self.model().index(0, 0)
                    self._view.setCurrentIndex(firstIndex)
                elif index != visitSearchIndex and index.row() == self.model().rowCount() - 1:
                    self._view.setCurrentIndex(visitSearchIndex)
                    self._view.scrollToTop()
                else:
                    row = min(self.model().rowCount() - 1, index.row() + step)
                    self._view.setCurrentIndex(self.model().index(row, 0))
                return True

            elif evtKey == Qt.Key_Delete:
                if index != visitSearchIndex and self._view.viewport().rect().contains(self._view.visualRect(index)):
                    self.indexDeleteRequested.emit(index)
                    return True

            elif evtKey == Qt.Key_Shift:
                self._delegate.setForceVisitItem(True)
                self._view.viewport().update()

            # end of switch evtKey

            if self.focusProxy():
                self.focusProxy().event(keyEvent)

            return True

        elif evtType == QEvent.KeyRelease:
            if evtKey == Qt.Key_Shift:
                self._delegate.setForceVisitItem(False)
                self._view.viewport().update()
                return True

        elif evtType in (QEvent.Wheel, QEvent.MouseButtonPress):
            if not self.underMouse():
                self.close()
                return False

        elif evtType == QEvent.FocusOut:
            # QFocusEvent
            focusEvent = event
            reason = focusEvent.reason()
            if reason != Qt.PopupFocusReason and reason != Qt.MouseFocusReason:
                self.close()

        elif evtType in (QEvent.Move, QEvent.Resize):
            w = obj
            if isinstance(w, QWidget) and w.isWindow() and self.focusProxy() and w == self.focusProxy().window():
                self.close()

        # end of switch evtType
        return False

    # Q_SIGNALS
    closed = pyqtSignal()
    searchEnginesDialogRequested = pyqtSignal()
    loadRequested = pyqtSignal(LoadRequest)

    indexActivated = pyqtSignal(QModelIndex)
    indexCtrlActivated = pyqtSignal(QModelIndex)
    indexShiftActivated = pyqtSignal(QModelIndex)
    indexDeleteRequested = pyqtSignal(QModelIndex)

    # public Q_SLOTS:
    def close(self):
        self.hide()
        self._view.verticalScrollBar().setValue(0)
        self._delegate.setForceVisitItem(False)
        self._forceResize = True

        self.closed.emit()

    # private:
    def _setupSearchEngines(self):
        for idx in (range(self._searchEnginesLayout.count())):
            item = self._searchEnginesLayout.takeAt(0)
            item.deleteLater()

        engines = gVar.app.searchEnginesManager().allEngines()
        for engine in engines:
            button = ToolButton(self)
            button.setIcon(engine.icon)
            button.setToolTip(engine.name)
            button.setAutoRaise(True)
            button.setIconSize(QSize(16, 16))

            def func():
                text = self.model().index(0, 0).data(LocationCompleterModel.SearchStringRole)
                self.loadRequested.emit(gVar.app.searchEngineManager().searchResult(engine, text))
            button.clicked.connect(func)
            self._searchEnginesLayout.addWidget(button)

    #def _openSearchEnginesDialog(self):
    #    pass
