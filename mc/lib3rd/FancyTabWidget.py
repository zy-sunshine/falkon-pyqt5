from PyQt5.Qt import QProxyStyle
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QPropertyAnimation
from PyQt5.Qt import QIcon
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import pyqtProperty
from PyQt5.Qt import QTimer
from PyQt5.QtWidgets import QTabBar
from PyQt5.Qt import QSize
from PyQt5.Qt import Qt
from PyQt5.Qt import QFontMetrics
from PyQt5.Qt import QSizePolicy
from PyQt5.Qt import QPainter
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.Qt import QRect
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QStyleOptionTab
from PyQt5.Qt import QLinearGradient
from PyQt5.Qt import QPoint
from PyQt5.Qt import QColor
from PyQt5.Qt import QTransform
from PyQt5.Qt import QFont
from PyQt5.Qt import QAbstractAnimation
from PyQt5.Qt import QPen
from PyQt5.Qt import QPalette
from PyQt5.Qt import QApplication
from PyQt5.Qt import QEvent
from PyQt5.Qt import QColorDialog
from PyQt5.Qt import QStackedLayout
from .StyleHelper import styleHelper
from mc.common import const

class FancyTabProxyStyle(QProxyStyle):
    # override
    def drawControl(self, element, option, painter, widget):
        '''
        @param: element ControlElement
        @param: option QStyleOption
        @param: painter QPainter
        @param: widget QWidget
        '''
        v_opt = option

        if element != self.CE_TabBarTab or not isinstance(v_opt, QStyleOptionTab):
            QProxyStyle.drawControl(element, option, painter, widget)
            return

        rect = v_opt.rect
        selected = v_opt.state & self.State_Selected
        vertical_tabs = v_opt.shape == QTabBar.RoundedWest
        text = v_opt.text

        if selected:
            # background
            painter.save()
            grad = QLinearGradient(rect.topLeft(), rect.topRight())
            grad.setColorAt(0, QColor(255, 255, 255, 140))
            grad.setColorAt(0, QColor(255, 255, 255, 210))
            painter.fillRect(rect.adjusted(0, 0, 0, -1), grad)
            painter.restore()

            # shadows
            painter.setPen(QColor(0, 0, 0, 110))
            painter.drawLine(rect.topLeft() + QPoint(1, -1), rect.topRight() - QPoint(0, 1))
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.setPen(QColor(0, 0, 0, 40))
            painter.drawLine(rect.topLeft(), rect.bottomLeft())

            # highlights
            painter.setPen(QColor(255, 255, 255, 50))
            painter.drawLine(rect.topLeft() + QPoint(0, -2), rect.topRight() - QPoint(0, 2))
            painter.drawLine(rect.bottomLeft() + QPoint(0, 1), rect.bottomRight() + QPoint(0, 1))
            painter.setPen(QColor(255, 255, 255, 40))
            painter.drawLine(rect.topLeft() + QPoint(0, 0), rect.topRight())
            painter.drawLine(rect.topRight() + QPoint(0, 1), rect.bottomRight() - QPoint(0, 1))
            painter.drawLine(rect.bottomLeft() + QPoint(0, -1), rect.bottomRight() - QPoint(0, 1))

        m = QTransform()
        if vertical_tabs:
            m = QTransform.fromTranslate(rect.left(), rect.bottom())
            m.rotate(-90)
        else:
            m = QTransform.fromTranslate(rect.left(), rect.top())

        draw_rect = QRect(QPoint(0, 0), m.mapRect(rect).size())

        painter.save()
        painter.setTransform(m)

        icon_rect = QRect(QPoint(8, 0), v_opt.iconSize)
        text_rect = QRect(icon_rect.topRight() + QPoint(4, 0), draw_rect.size())
        text_rect.setRight(draw_rect.width())
        icon_rect.translate(0, (draw_rect.height() - icon_rect.height()) / 2)

        boldFont = QFont(painter.font())
        boldFont.setPointSizeF(styleHelper.sidebarFontSize())
        boldFont.setBold(True)
        painter.setFont(boldFont)
        painter.setPen(selected and QColor(255, 255, 255, 160) or QColor(0, 0, 0, 110))
        textFlags = Qt.AlignHCenter | Qt.AlignVCenter
        painter.drawText(text_rect, textFlags, text)
        painter.setPen(selected and QColor(60, 60, 60) or styleHelper.panelTextColor())
        if widget:
            fader_key = 'tab_' + text + '_fader'
            animation_key = 'tab_' + text + '_animation'

            tab_hover = widget.property('tab_hover')
            # int
            fader = widget.property(fader_key)
            # QPropertyAnimation
            animation = widget.property(animation_key)

            if not animation:
                mut_widget = widget
                fader = 0
                mut_widget.setProperty(fader_key, fader)
                animation = QPropertyAnimation(mut_widget, fader_key, mut_widget)
                animation.valueChanged.connect(mut_widget.update)
                mut_widget.setProperty(animation_key, animation)

            if text == tab_hover:
                if animation.state() != QAbstractAnimation.Running and fader != 40:
                    animation.stop()
                    animation.setDuration(80)
                    animation.setEndValue(40)
                    animation.start()
            else:
                if animation.state() != QAbstractAnimation.Running and fader != 0:
                    animation.stop()
                    animation.setDuration(160)
                    animation.setEndValue(0)
                    animation.start()

            if not selected:
                painter.save()
                painter.fillRect(draw_rect, QColor(255, 255, 255, fader))
                painter.setPen(QPen(QColor(255, 255, 255, fader), 1.0))
                painter.drawLine(draw_rect.topLeft(),
                    vertical_tabs and draw_rect.bottomLeft() or draw_rect.topRight())
                painter.drawLine(draw_rect.bottomRight(),
                    vertical_tabs and draw_rect.topRight() or draw_rect.bottomLeft())
                painter.restore()

        if selected:
            iconMode = QIcon.Selected
        else:
            iconMode = QIcon.Normal
        styleHelper.drawIconWithShadow(v_opt.icon, icon_rect, painter, iconMode)

        painter.drawText(text_rect.translated(0, -1), textFlags, text)

        painter.restore()

    # override
    def polish(self, obj):
        '''
        @param: obj QWidget
        @param: obj QApplication
        @param: obj QPalette
        '''
        if isinstance(obj, QWidget):
            if obj.metaObject().className() == QTabBar:
                obj.setMouseTracking(True)
                obj.installEventFilter(self)
            super().polish(obj)
        elif isinstance(obj, QApplication):
            super().polish(obj)
        elif isinstance(obj, QPalette):
            super().polish(obj)

    # protected:
    # override
    def eventFilter(self, obj, event):
        '''
        @param: obj QObject
        @param: event QEvent
        '''
        bar = obj
        evtType = event.type()
        if isinstance(bar, QTabBar) and evtType == QEvent.MouseMove or evtType == QEvent.Leave:
            old_hovered_tab = bar.property('tab_hover')
            if evtType == QEvent.Leave:
                hovered_tab = ''
            else:
                hovered_tab = bar.tabText(bar.tabAt(event.pos()))
                bar.setProperty('tab_hover', hovered_tab)

                if old_hovered_tab != hovered_tab:
                    bar.update()

        return False

class FancyTab(QWidget):
    def __init__(self, tabbar):
        '''
        @param: tabbar QWidget
        '''
        super().__init__(tabbar)
        self.icon = QIcon()
        self.text = ''
        self._animator = QPropertyAnimation()
        self._tabbar = tabbar  # QWidget
        self._fader = 0.0

        self._animator.setPropertyName(b'fader')
        self._animator.setTargetObject(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

    def fader(self):
        '''
        @return: float
        '''
        return self._fader

    def setFader(self, value):
        '''
        @param: value float
        '''
        self._fader = value
        self._tabbar.update()

    fader = pyqtProperty(float, fader, setFader)

    # override
    def sizeHint(self):
        '''
        @return: QSize
        '''
        boldFont = QFont(self.font())
        boldFont.setPointSizeF(styleHelper.sidebarFontSize())
        boldFont.setBold(True)
        fm = QFontMetrics(boldFont)
        spacing = 8
        width = 60 + spacing + 2
        iconHeight = 32
        ret = QSize(width, iconHeight + spacing + fm.height())
        return ret

    def fadeIn(self):
        self._animator.stop()
        self._animator.setDuration(80)
        self._animator.setEndValue(40)
        self._animator.start()

    def fadeOut(self):
        self._animator.stop()
        self._animator.setDuration(160)
        self._animator.setEndValue(0)
        self._animator.start()

    # protected:
    # override
    def enterEvent(self, event):
        self.fadeIn()

    # override
    def leaveEvent(self, event):
        self.fadeOut()

class FancyTabBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rounding = 22
        self._textPadding = 4
        self._currentIndex = 0
        self._tabs = []  # QList<FancyTab>
        self._triggerTimer = QTimer()

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # setStyle(new QWindowsStyle)
        self.setMinimumWidth(max(2 * self._rounding, 40))
        self.setAttribute(Qt.WA_Hover, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)  # Needed for hover events
        self._triggerTimer.setSingleShot(True)

        layout = QVBoxLayout()
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Expanding))
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # We use a zerotimer to keep the sidebar responsing
        self._triggerTimer.timeout.connect(self.emitCurrentIndex)

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        p = QPainter(self)

        currentIndex = self.currentIndex()
        for idx in range(self.count()):
            if idx != currentIndex:
                self.paintTab(p, idx)

        # paint active tab last, since it overlaps the neighbors
        if currentIndex != -1:
            self.paintTab(p, currentIndex)

    #override
    def paintTab(self, painter, tabIndex):
        '''
        @param: painter QPainter
        @param: tabIndex int
        '''
        if not self.validIndex(tabIndex):
            print('Warning: invalid index %s' % tabIndex)
            return

        painter.save()

        rect = self.tabRect(tabIndex)
        selected = (tabIndex == self._currentIndex)

        if selected:
            # background
            painter.save()
            grad = QLinearGradient(rect.topLeft(), rect.topRight())
            grad.setColorAt(0, QColor(255, 255, 255, 140))
            grad.setColorAt(1, QColor(255, 255, 255, 210))
            painter.fillRect(rect.adjusted(0, 0, 0, -1), grad)
            painter.restore()

            # shadows
            painter.setPen(QColor(0, 0, 0, 110))
            painter.drawLine(rect.topLeft() + QPoint(1, -1), rect.topRight() - QPoint(0, 1))
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.setPen(QColor(0, 0, 0, 40))
            painter.drawLine(rect.topLeft(), rect.bottomLeft())

            # highlights
            painter.setPen(QColor(255, 255, 255, 50))
            painter.drawLine(rect.topLeft() + QPoint(0, -2), rect.topRight() - QPoint(0, 2))
            painter.drawLine(rect.bottomLeft() + QPoint(0, 1), rect.bottomRight() + QPoint(0, 1))
            painter.setPen(QColor(255, 255, 255, 40))
            painter.drawLine(rect.topLeft() + QPoint(0, 0), rect.topRight())
            painter.drawLine(rect.topRight() + QPoint(0, 1), rect.bottomRight() - QPoint(0, 1))
            painter.drawLine(rect.bottomLeft() + QPoint(0, -1), rect.bottomRight() - QPoint(0, 1))

        # QString tabText(painter->fontMetrics().elidedText(this->tabText(tabIndex), Qt::ElideMiddle, width()));
        tabTextRect = self.tabRect(tabIndex)
        tabIconRect = QRect(tabTextRect)
        tabIconRect.adjust(+4, +4, -4, -4)
        tabTextRect.translate(0, -2)
        boldFont = QFont(painter.font())
        boldFont.setPointSizeF(styleHelper.sidebarFontSize())
        boldFont.setBold(True)
        painter.setFont(boldFont)
        painter.setPen(selected and QColor(255, 255, 255, 160) or QColor(0, 0, 0, 110))
        # int textFlags = Qt::AlignCenter | Qt::AlignBottom
        # painter->drawText(tabTextRect, textFlags, tabText)
        painter.setPen(selected and QColor(60, 60, 60) or styleHelper.panelTextColor())

        if not const.OS_MACOS:
            if not selected:
                painter.save()
                fader = int(self._tabs[tabIndex].fader)
                grad = QLinearGradient(rect.topLeft(), rect.topRight())
                grad.setColorAt(0, Qt.transparent)
                grad.setColorAt(0.5, QColor(255, 255, 255, fader))
                grad.setColorAt(1, Qt.transparent)
                # painter.fillRect(rect, grad)
                # painter.setPen(QPen(grad, 1.0))
                painter.fillRect(rect, QColor(255, 255, 255, fader))
                painter.setPen(QPen(QColor(255, 255, 255, fader), 1.0))
                painter.drawLine(rect.topLeft(), rect.topRight())
                painter.drawLine(rect.bottomLeft(), rect.bottomRight())
                painter.restore()

        # const int textHeight = painter->fontMetrics().height();
        tabIconRect.adjust(0, 6, 0, -6)
        if selected:
            iconMode = QIcon.Selected
        else:
            iconMode = QIcon.Normal
        styleHelper.drawIconWithShadow(self.tabIcon(tabIndex), tabIconRect, painter, iconMode)

        painter.translate(0, -1)
        # painter->drawText(tabTextRect, textFlags, tabText)
        painter.restore()

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        event.accept()
        for index in range(len(self._tabs)):
            if self.tabRect(index).contains(event.pos()):
                self._currentIndex = index
                self.update()
                self._triggerTimer.start(0)
                break

    def validIndex(self, index):
        return index >= 0 and index < len(self._tabs)

    # override
    def sizeHint(self):
        '''
        @return: QSize
        '''
        sh = self._tabSizeHint()
        return QSize(sh.width(), sh.height() * len(self._tabs))

    # override
    def minimumSizeHint(self):
        '''
        @param: QSize
        '''
        sh = self._tabSizeHint(True)
        return QSize(sh.width(), sh.height() * len(self._tabs))

    def addTab(self, icon, label):
        '''
        @param: icon QIcon
        @param: label QString
        '''
        tab = FancyTab(self)
        tab.icon = icon
        tab.text = label
        self._tabs.append(tab)
        # layout QVBoxLayout
        self.layout().insertWidget(self.layout().count() - 1, tab)

    def addSpacer(self, size):
        '''
        @param: size int
        '''
        # layout QVBoxLayout
        self.layout().insertSpacerItem(self.layout.count() - 1,
            QSpacerItem(0, size, QSizePolicy.Fixed, QSizePolicy.Maximum))

    def removeTab(self, index):
        '''
        @param: index int
        '''
        self._tabs.pop(index)

    def setCurrentIndex(self, index):
        '''
        @param: index int
        '''
        self._currentIndex = index
        self.update()
        self.currentChanged.emit(self._currentIndex)

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
        self._tabs[index].setToolTip(toolTip)

    def tabToolTip(self, index):
        '''
        @return: QString
        '''
        return self._tabs[index].toolTip()

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
        return self._tabs[index].geometry()

    # Q_SIGNALS:
    currentChanged = pyqtSignal(int)

    # public Q_SLOTS:
    def emitCurrentIndex(self):
        '''
        @note: This keeps the sidebar responsive since we get a repaint before
            loading the mode itself
        '''
        self.currentChanged.emit(self._currentIndex)

    # private:
    def _tabSizeHint(self, minimum=False):
        '''
        @return: QSize
        '''
        boldFont = QFont(self.font())
        boldFont.setPointSizeF(styleHelper.sidebarFontSize())
        boldFont.setBold(True)
        fm = QFontMetrics(boldFont)
        spacing = 8
        width = 60 + spacing + 2
        if minimum:
            iconHeight = 0
        else:
            iconHeight = 32
        return QSize(width, iconHeight + spacing + fm.height())

class FancyColorButton(QWidget):
    '''
    @note: not finished yet
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.m_parent = parent
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event MouseEvent
        '''
        if event.modifiers() & Qt.ShiftModifier:
            styleHelper.setBaseColor(QColorDialog.getColor(styleHelper.requestedBaseColor(), self._parent))

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
        self._stack = QStackedLayout()  # QStackedLayout
        self._background_pixmap = QPixmap()
        self._side_widget = QWidget()  # QWidget
        self._side_layout = QVBoxLayout()  # QVBoxLayout
        self._top_layout = QVBoxLayout()  # QVBoxLayout

        self._use_background = False  # bool

        self._menu = None  # QMenu

        self._proxy_style = FancyTabProxyStyle()  # FancyTabProxyStyle

        self._side_layout.setSpacing(0)
        self._side_layout.setContentsMargins(0, 0, 0, 0)
        self._side_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Expanding))

        self._side_widget.setLayout(self._side_layout)
        self._side_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

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
        self._items.append(self.Item(icon, label))

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
        return self._mode

    def bgPixmap(self):
        '''
        @return: QPixmap
        '''
        return self._background_pixmap

    bgPixmap = pyqtProperty(QPixmap, bgPixmap, SetBackgroundPixmap)

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
        elif mode == self.Mode_Tabs:
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
        self.update()

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
        styleHelper.verticalGradient(painter, rect, rect)

        if not self._background_pixmap.isNull():
            pixmap_rect = QRect(self._background_pixmap.rect())
            pixmap_rect.moveTo(rect.topLeft())

            while pixmap_rect.top() < rect.bottom():
                source_rect = QRect(pixmap_rect.intersected(rect))
                source_rect.moveTo(0, 0)
                painter.drawPixmap(pixmap_rect.topLeft(), self._background_pixmap, source_rect)
                pixmap_rect.moveTop(pixmap_rect.bottom() - 10)

        painter.setPen(styleHelper.borderColor())
        painter.drawLine(rect.topRight(), rect.bottomRight())

        # QColor
        light = styleHelper.sidebarHighlight()
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
