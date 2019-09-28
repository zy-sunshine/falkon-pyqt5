from PyQt5.Qt import QProxyStyle
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QPropertyAnimation
from PyQt5.Qt import QIcon
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QTimer
from PyQt5.QtWidgets import QTabBar
from PyQt5.Qt import QSize
from PyQt5.Qt import Qt
from PyQt5.Qt import QFontMetrics
from PyQt5.Qt import QSizePolicy
from PyQt5.Qt import QPainter

class FancyTabProxyStyle(QProxyStyle):
    # override
    def drawControl(self, element, option, painter, widget):
        '''
        @param: element ControlElement
        @param: option QStyleOption
        @param: painter QPainter
        @param: widget QWidget
        '''
        pass

    # override
    def polish(self, obj):
        '''
        @param: obj QWidget
        @param: obj QApplication
        @param: obj QPalette
        '''
        pass

    # protected:
    # override
    def eventFilter(self, obj, event):
        '''
        @param: obj QObject
        @param: event QEvent
        '''
        pass

class FancyTab(QWidget):
    def __init__(self, tabbar):
        '''
        @param: tabbar QWidget
        '''
        super().__init__(tabbar)
        self.icon = QIcon()
        self.text = ''
        self._animator = QPropertyAnimation()
        self._tabbar = None  # QWidget
        self._fader = 0.0

    def fader(self):
        '''
        @return: float
        '''
        return self._fader

    def setFader(self, value):
        '''
        @param: value float
        '''
        pass

    # override
    def sizeHint(self):
        '''
        @return: QSize
        '''
        pass

    def fadeIn(self):
        pass

    def fadeOut(self):
        pass

    # protected:
    # override
    def enterEvent(self, event):
        pass

    # override
    def leaveEvent(self, event):
        pass

class FancyTabBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rounding = 22
        self._textPadding = 4
        self._currentIndex = 0
        self._tabs = []  # QList<FancyTab>
        self._triggerTimer = QTimer()

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        pass

    #override
    def paintTab(self, painter, tabIndex):
        '''
        @param: painter QPainter
        @param: tabIndex int
        '''
        pass

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass

    def validIndex(self, index):
        return index >= 0 and index < len(self._tabs)

    # override
    def sizeHint(self):
        '''
        @return: QSize
        '''
        pass

    # override
    def minimumSizeHint(self):
        '''
        @param: QSize
        '''
        pass

    def addTab(self, icon, label):
        '''
        @param: icon QIcon
        @param: label QString
        '''
        pass

    def addSpacer(self, size):
        '''
        @param: size int
        '''
        pass

    def removeTab(self, index):
        '''
        @param: index int
        '''
        self._tabs.pop(index)

    def setCurrentIndex(self, index):
        '''
        @param: index int
        '''
        pass

    def currentIndex(self):
        '''
        @return: int
        '''
        return self._currentIndex

    def setTabToolTip(self, index, toolTip):
        '''
        @param: index int
        @param: toolTip QString
        '''
        pass

    def tabToolTip(self):
        '''
        @return: QString
        '''
        pass

    def tabIcon(self, index):
        '''
        @return: QIcon
        '''
        return self._tabs[index].icon

    def tabText(self, index):
        '''
        @return: QStirng
        '''
        return self._tabs[index].text

    def count(self):
        return len(self._tabs)

    def tabRect(self, index):
        pass

    # Q_SIGNALS:
    currentChanged = pyqtSignal(int)

    # public Q_SLOTS:
    def emitCurrentIndex(self):
        pass

    # private:
    def _tabSizeHint(self, minimum=False):
        '''
        @return: QSize
        '''
        pass

class FancyTabWidget(QWidget):
    # Values are persisted = only add to the end
    # enum Mode
    Mode_None = 0
    Mode_LargeSidebar = 1
    Mode_SmallSidebar = 2
    Mode_Tabs = 3
    Mode_IconOnlyTabs = 4
    Mode_PlainSidebar = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = self.Mode_None
        self._items = []  # QList<Item>

        self._tab_bar = None  # QWidget
        self._stack = None  # QStackedLayout
        self._background_pixmap = QPixmap()
        self._side_widget = None  # QWidget
        self._side_layout = None  # QVBoxLayout
        self._top_layout = None  # QVBoxLayout

        self._use_background = False  # bool

        self._menu = None  # QMenu

        self._proxy_style = None  # FancyTabProxyStyle

        self._side_layout.setSpacing(0)
        self._side_layout.setContentsMargins(0, 0, 0, 0)
        self._side_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Expanding))

        self._side_widget.setLayout(self._side_layout)
        self._side_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.ExpandFlag)

        self._top_layout.setSpacing(0)
        self._top_layout.setContentsMargins(0, 0, 0, 0)
        self._top_layout.addLayout(self._stack)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)
        main_layout.addWidget(self._side_widget)
        main_layout.addLayout(self._top_layout)
        self.setLayout(main_layout)

    class Item:
        # enum Type
        Type_Tab = 0
        Type_Spacer = 1
        def __init__(self, icon, label):
            '''
            @param: icon QIcon
            @param: label QString
            '''
            self.type = self.Type_Tab  # Type
            self.tab_label = label  # QString
            self.tab_icon = icon  # QIcon
            self.spacer_size = 0

    def AddTab(self, tab, icon, label):
        '''
        @param: tab QWidget
        @param: icon Qicon
        @param: label QString
        '''
        self._stack.addWidget(tab)
        self._items.append(self._Item(icon, label))

    def AddSpacer(self, size=40):
        self._items.append(self.Item(size))

    def SetBackgroundPixmap(self, pixmap):
        '''
        @param: pixmap QPixmap
        '''
        self._background_pixmap = pixmap
        self.update()

    def AddBottomWidget(self, widget):
        '''
        @param: widget QWidget
        '''
        self._top_layout.addWidget(widget)

    def current_index(self):
        '''
        @return: int
        '''
        return self._stack.currentIndex()

    def mode(self):
        '''
        @return: Mode
        '''
        return self.mode_

    def bgPixmap(self):
        '''
        @return: QPixmap
        '''
        return self.background_pixmap_

    # public Q_SLOTS:
    def SetCurrentIndex(self, index):
        bar = self._tab_bar
        if isinstance(bar, FancyTabBar):
            bar.setCurrentIndex(index)
        elif isinstance(bar, QTabBar):
            bar.setCurrentIndex(index)
        else:
            self._stack.setCurrentIndex(index)

    def SetMode(self, mode):
        # Remove previous tab bar
        del self._tab_bar
        self._tab_bar = None

        self._use_background = False

        # Create new tab bar
        if mode == self.Mode_None:
            pass
        elif mode == self.Mode_LargeSidebar:
            bar = FancyTabBar(self)
            self._side_layout.insertWidget(0, bar)
            self._tab_bar = bar
            for item in self._items:
                if item.type == self.Item.Type_Spacer:
                    bar.addSpacer(item.spacer_size)
                else:
                    bar.addTab(item.tab_icon, item.tab_label)

            bar.setCurrentIndex(self._stack.currentIndex())
            bar.currentChanged.connect(self._ShowWidget)
            self._use_background = True
        elif mode = self.Mode_Tabs:
            self._MakeTabBar(QTabBar.RoundedNorth, True, False, False)
        elif mode == self.Mode_IconOnlyTabs:
            self._MakeTabBar(QTabBar.RoundedNorth, False, True, False)
        elif mode == self.Mode_SmallSidebar:
            self._MakeTabBar(QTabBar.RoundedWest, True, True, True)
            self._use_background = True
        elif mode == self.Mode_PlainSidebar:
            self._MakeTabBar(QTabBar.RoundedWest, True, True, False)
        else:
            print('DEBUG: Unknown fancy tab mode %s' % mode)

        self._tab_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self._mode = mode
        self.ModeChanged.emit(mode)
        self.upate()

    # Q_SIGNALS:
    CurrentChanged = pyqtSignal(int)  # index
    ModeChanged = pyqtSignal(int)  # mode FancyTabWidget::Mode

    # protected:
    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        if not self._use_background:
            return

        painter = QPainter(self)

        rect = self._side_widget.rect().adjusted(0, 0, 1, 0)
        rect = self.style().visualRect(self.layoutDirection(), self.geometry(), rect)
        Utils.StyleHelper.verticalGradient(painter, rect, rect)

        if not self._background_pixmap.isNull():
            pixmap_rect = QRect(self._background_pixmap.rect())
            pixmap_rect.moveTo(rect.topLeft())

            while pixmap_rect.top() < rect.bottom():
                source_rect = QRect(pixmap_rect.intersected(rect))
                source_rect.moveTo(0, 0)
                painter.drawPixmap(pixmap_rect.topLeft(), self._background_pixmap, source_rect)
                pixmap_rect.moveTop(pixmap_rect.bottom() - 10)

        painter.setPen(Utils.StyleHelper.borderColor())
        painter.drawLine(rect.topRight(), rect.bottomRight())

        # QColor
        light = Utils.StyleHelper.sidebarHighlight()
        painter.setPen(light)
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass

    # private Q_SLOTS:
    def _ShowWidget(self, index):
        self._stack.setCurrentIndex(index)
        self.CurrentChanged.emit(index)

    # private:
    def _MakeTabBar(self, shap, text, icons, fancy):
        '''
        @param: shap QTabBar::Shap
        @param: text bool
        @param: icons bool
        @param: fancy bool
        '''
        bar = QTabBar(self)
        bar.setShape(shap)
        bar.setDocumentMode(True)
        bar.setUsesScrollButtons(True)

        if shap == QTabBar.RoundedWest:
            bar.setIconSize(QSize(22, 22))

        if fancy:
            bar.setStyle(self._proxy_style)

        if shap == QTabBar.RoundedNorth:
            self._top_layout.insertWidget(0, bar)
        else:
            self._side_layout.insertWidget(0, bar)

        # Item
        for item in self._items:
            if item.type != self.Item.Type_Tab:
                continue

            label = item.tab_label
            if shap == QTabBar.RoundedWest:
                label = QFontMetrics(self.font()).elidedText(label, Qt.ElideMiddle, 100)

            tab_id = -1
            if icons and text:
                tab_id = bar.addTab(item.tab_icon, label)
            elif icons:
                tab_id = bar.addTab(item.tab_icon, '')
            elif text:
                tab_id = bar.addTab(label)

            bar.setTabToolTip(tab_id, item.tab_label)

        bar.setCurrentIndex(self._stack.currentIndex())
        bar.currentChanged.connect(self._ShowWidget)
        self._tab_bar = bar

    def _AddMenuItem(self, mapper, group, text, mode):
        '''
        @param: mapper QSignalMapper
        @param: group QActionGroup
        @param: text QString
        @param: mode Mode
        '''
        # QAction
        action = group.addAction(text)
        action.setCheckable(True)
        mapper.setMapping(action, mode)
        action.triggered.connect(mapper.map)

        if mode == self._mode:
            action.setChecked(True)
