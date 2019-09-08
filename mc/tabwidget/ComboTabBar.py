from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QTabBar
from PyQt5.Qt import QColor
from PyQt5.Qt import QPoint
from PyQt5.QtWidgets import QScrollBar
from PyQt5.Qt import QEasingCurve
from PyQt5.QtWidgets import QAbstractButton
from PyQt5.Qt import Qt
from PyQt5.Qt import QStyle
from PyQt5.Qt import QSize
from PyQt5.Qt import QPainter
from PyQt5.Qt import QStyleOption
from PyQt5.Qt import QStyleOptionTab
from PyQt5.Qt import QStyleOptionTabBarBase
from PyQt5.Qt import QCursor
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.Qt import QIcon
from PyQt5.Qt import QTimer
from PyQt5.Qt import QEvent
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QPalette
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QPropertyAnimation
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QFrame
from PyQt5.Qt import QRect
from PyQt5.Qt import QStylePainter
from PyQt5.Qt import QMouseEvent
from PyQt5.Qt import pyqtProperty
from mc.tools.ToolButton import ToolButton
from mc.tools.WheelHelper import WheelHelper
from mc.common.globalvars import gVar
from .TabIcon import TabIcon

class TabBarHelper(QTabBar):
    def __init__(self, isPinnedTabBar, comboTabBar):
        super(TabBarHelper, self).__init__(comboTabBar)
        self._comboTabBar = comboTabBar
        self._scrollArea = None  # QScrollArea
        self._tabPadding = -1
        self._baseColor = QColor()
        self._pressedIndex = -1
        self._dragInProgress = False
        self._dragStartPosition = QPoint()
        self._movingTab = None  # QMovableTabWidget
        self._activeTabBar = False
        self._isPinnedTabBar = isPinnedTabBar
        self._useFastTabSizeHint = False
        self._dropIndicatorIndex = -1
        self._dropIndicatorPosition = 0  # ComboTabBar::DropIndicatorPosition

    def tabPadding(self):
        return self._tabPadding

    def setTabPadding(self, padding):
        self._tabPadding = padding

    tabPadding = pyqtProperty(int, tabPadding, setTabPadding)

    def baseColor(self):
        return self._baseColor

    def setBaseColor(self, color):
        self._baseColor = color

    baseColor = pyqtProperty(QColor, baseColor, setBaseColor)

    def setTabButton(self, index, position, widget):
        '''
        @param: index int
        @param: position QTabBar::ButtonPosition
        @param: widget QWidget
        '''
        super(TabBarHelper, self).setTabButton(index, position, widget)

    # override
    def tabSizeHint(self, index):
        '''
        @return: QSize
        '''
        if self == self._comboTabBar.mainTabBar():
            index += self._comboTabBar.pinnedTabsCount()
        result = self._comboTabBar.tabSizeHint(index, self._useFastTabSizeHint)
        return result

    def baseClassTabSizeHint(self, index):
        '''
        @return: QSize
        '''
        return super(TabBarHelper, self).tabSizeHint(index)

    def draggedTabRect(self):
        '''
        @return: Rect
        '''
        if not self._dragInProgress:
            return QRect()

        tab = QStyleOptionTab()
        self._initStyleOption(tab, self._pressedIndex)

        tabDragOffset = self._dragOffset(tab, self._pressedIndex)
        if tabDragOffset != 0:
            tab.rect.moveLeft(tab.rect.x() + tabDragOffset)
        return tab.rect

    def tabPixmap(self, index):
        '''
        @return: QPixmap
        '''
        tab = QStyleOptionTab()
        self._initStyleOption(tab, index)

        tab.state &= ~QStyle.State_MouseOver
        tab.position = QStyleOptionTab.OnlyOneTab
        tab.leftButtonSize = QSize()
        tab.rightButtonSize = QSize()

        iconButton = self.tabButton(index, self._comboTabBar.iconButtonPosition())
        closeButton = self.tabButton(index, self._comboTabBar.closeButtonPosition())

        if iconButton:
            pix = iconButton.grab()
            if not pix.isNull():
                tab.icon = pix
                tab.iconSize = pix.size() / pix.devicePixelRatioF()

        if closeButton:
            width = tab.fontMetrics.width(tab.text) + closeButton.width()
            tab.text = tab.fontMetrics.elidedText(self.tabText(index), Qt.ElideRight, width)

        out = QPixmap(tab.rect.size() * self.devicePixelRatioF())
        out.setDevicePixelRatio(self.devicePixelRatioF())
        out.fill(Qt.transparent)
        tab.rect = QRect(QPoint(0, 0), tab.rect.size())

        p = QPainter(out)
        self.style().drawControl(QStyle.CE_TabBarTab, tab, p, self)
        p.end()

        return out

    def isActiveTabBar(self):
        return self._activeTabBar

    def setActiveTabBar(self, activate):
        if self._activeTabBar != activate:
            self._activeTabBar = activate

            # If the last tab in a tabbar is closed, the selection jumps to the
            # other tabbar. The stacked widget automatically selects the next
            # tab, which is either the last tab in pinned tabbar or the first
            # the first one in main tabbar.

            if not self._activeTabBar:
                self._comboTabBar._blockCurrentChangedSignal = True
                if self._isPinnedTabBar:
                    index = self.count() - 1
                else:
                    index = 0
                self.setCurrentIndex(index)
                self._comboTabBar._blockCurrentChangedSignal = False

            self.update()

    def removeTab(self, index):
        '''
        @note: Removing tab in inative tabbar will change current index and thus
            changing active tabbar, which is really not wanted.
            Also removing tab will cause a duplicate call to ComboTabBar::slotCurrentChanged()
        '''
        self._comboTabBar._blockCurrentChangedSignal = True

        super(TabBarHelper, self).removeTab(index)

        self._comboTabBar._blockCurrentChangedSignal = False

    def setScrollArea(self, scrollArea):
        '''
        @param: scrollArea QScrollArea
        '''
        self._scrollArea = scrollArea

    def useFastTabSizeHint(self, enabled):
        self._useFastTabSizeHint = enabled

    def showDropIndicator(self, index, position):
        '''
        @param: position ComboTabBar::DropIndicatorPosition
        '''
        self._dropIndicatorIndex = index
        self._dropIndicatorPosition = position
        self.update()

    def clearDropIndicator(self):
        self._dropIndicatorIndex = -1
        self.update()

    def isDisplayedOnViewPort(self, globalLeft, globalRight):
        '''
        @params: int
        '''
        isVisible = True

        if self._scrollArea:
            if globalRight < self._scrollArea.viewport().mapToGlobal(QPoint(0, 0)).x() or \
                    globalLeft > self._scrollArea.viewport().mapToGlobal(
                        self._scrollArea.viewport().rect().topRight()).x():
                isVisible = False

        return isVisible

    def isDragInProgress(self):
        return self._dragInProgress

    @classmethod
    def initStyleBaseOption(cls, optTabBase, tabBar, size):
        '''
        @param: optTabBase QStyleOptionTabBarBase
        @param: tabBar QTabBar
        @param: size QSize
        '''
        tabOverlap = QStyleOptionTab()
        tabOverlap.shape = tabBar.shape()
        overlap = tabBar.style().pixelMetric(QStyle.PM_TabBarBaseOverlap, tabOverlap, tabBar)
        theParent = tabBar.parentWidget()
        optTabBase.initFrom(tabBar)
        optTabBase.shape = tabBar.shape()
        optTabBase.documentMode = tabBar.documentMode()
        if theParent and overlap > 0:
            rect = QRect()
            if tabOverlap.shape in (QTabBar.RoundedNorth, QTabBar.TriangularNorth):
                rect.setRect(0, size.height() - overlap, size.width(), overlap)
            elif tabOverlap.shape in (QTabBar.RoundedSouth, QTabBar.TriangularSouth):
                rect.setRect(0, 0, size.width(), overlap)
            elif tabOverlap.shape in (QTabBar.RoundedEast, QTabBar.TriangularEast):
                rect.setRect(0, 0, overlap, size.height())
            elif tabOverlap.shape in (QTabBar.RoundedWest, QTabBar.TriangularWest):
                rect.setRect(size.width() - overlap, 0, overlap, size.height())
            optTabBase.rect = rect

    # public Q_SLOTS:
    def setCurrentIndex(self, index):
        if index == self.currentIndex() and not self._activeTabBar:
            self.currentChanged.emit(self.currentIndex())

        super(TabBarHelper, self).setCurrentIndex(index)

    # private:
    # override
    def event(self, event):
        '''
        @param: event QEvent
        '''
        if event.type() == QEvent.ToolTip:
            event.ignore()
            return False

        super(TabBarHelper, self).event(event)
        event.ignore()
        return False

    # override
    def paintEvent(self, event):  # noqa C901
        '''
        @param: event QPaintEvent
        '''
        optTabBase = QStyleOptionTabBarBase()
        self.initStyleBaseOption(optTabBase, self, self.size())

        p = QStylePainter(self)
        selected = self.currentIndex()

        for idx in range(self.count()):
            optTabBase.tabBarRect |= self.tabRect(idx)

        if self._activeTabBar:
            optTabBase.selectedTabRect = self.tabRect(selected)

        if self.drawBase():
            p.drawPrimitive(QStyle.PE_FrameTabBarBase, optTabBase)

        cursorPos = QCursor.pos()
        indexUnderMouse = -1
        if self.isDisplayedOnViewPort(cursorPos.x(), cursorPos.x()):
            indexUnderMouse = self.tabAt(self.mapFromGlobal(cursorPos))

        for idx in range(self.count()):
            if idx == selected:
                continue

            tab = QStyleOptionTab()
            self._initStyleOption(tab, idx)

            tabDragOffset = self._dragOffset(tab, idx)
            if tabDragOffset != 0:
                tab.rect.moveLeft(tab.rect.x() + tabDragOffset)

            # Don't bother drawing a tab if the entire tab is outside of the
            # visible tab bar.
            if not self.isDisplayedOnViewPort(self.mapToGlobal(tab.rect.topLeft()).x(),
                self.mapToGlobal(tab.rect.topRight()).x()
            ):
                continue

            if not self._activeTabBar:
                tab.selectedPosition = QStyleOptionTab.NotAdjacent

            if not (tab.state & QStyle.State_Enabled):
                tab.palette.setCurrentColorGroup(QPalette.Disabled)

            # Update mouseover state when scrolling
            if not self._dragInProgress and idx == indexUnderMouse:
                tab.state |= QStyle.State_MouseOver
            else:
                tab.state &= ~QStyle.State_MouseOver

            p.drawControl(QStyle.CE_TabBarTab, tab)

        # Draw the selected tab last to get it "on top"
        if selected >= 0:
            tab = QStyleOptionTab()
            self._initStyleOption(tab, selected)

            tabDragOffset = self._dragOffset(tab, selected)
            if tabDragOffset != 0:
                tab.rect.moveLeft(tab.rect.x() + tabDragOffset)

            # Update mouseover state when scrolling
            if selected == indexUnderMouse:
                tab.state |= QStyle.State_MouseOver
            else:
                tab.state &= ~QStyle.State_MouseOver

            if not self._activeTabBar:
                # If this is inactive tab, we still need to draw selected tab
                # outside the tabbar. Some themes (eg. Oxygen) draw line under
                # tabs with selected tab. Let's just move it outside rect(), it
                # appears to work
                tb = QStyleOptionTab(tab)
                tb.rect.moveRight((self.rect().x() + self.rect().width()) * 2)
                p.drawControl(QStyle.CE_TabBarTab, tb)

                # Draw the tab without selected state
                tab.state = tab.state & ~QStyle.State_Selected

            if not self._movingTab or not self._movingTab.isVisible():
                p.drawControl(QStyle.CE_TabBarTab, tab)
            else:
                taboverlap = self.style().pixelMetric(QStyle.PM_TabBarTabOverlap, None, self)
                self._movingTab.setGeometry(tab.rect.adjusted(-taboverlap, 0, taboverlap, 0))

                grabRect = self.tabRect(selected)
                grabRect.adjust(-taboverlap, 0, taboverlap, 0)
                grabImage = QPixmap(grabRect.size() * self.devicePixelRatioF())
                grabImage.setDevicePixelRatio(self.devicePixelRatioF())
                grabImage.fill(Qt.transparent)
                p = QStylePainter(grabImage, self)
                # p.initFrom(self)
                if tabDragOffset != 0:
                    tab.position = QStyleOptionTab.OnlyOneTab
                tab.rect.moveTopLeft(QPoint(taboverlap, 0))
                p.drawControl(QStyle.CE_TabBarTab, tab)
                self._movingTab._pixmap = grabImage
                self._movingTab.update()

        # Draw drop indicator
        if self._dropIndicatorIndex != -1:
            tr = self.tabRect(self._dropIndicatorIndex)
            r = QRect()
            if self._dropIndicatorPosition == ComboTabBar.BeforTab:
                r = QRect(max(0, tr.left() - 1), tr.top(), 3, tr.height())
            else:
                rightOffset = self._dropIndicatorIndex == self.count() - 1
                r = QRect(tr.right() + rightOffset, tr.top(), 3, tr.height())
                gVar.appTools.paintDropIndicator(self, r)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        event.ignore()
        if event.buttons() == Qt.LeftButton:
            self._pressedIndex = self.tabAt(event.pos())
            if self._pressedIndex != -1:
                self._dragStartPosition = event.pos()
                # virtualize selecting tab by click
                if self._pressedIndex == self.currentIndex() and not self._activeTabBar:
                    self.emit(self.currentIndex())

        super(TabBarHelper, self).mousePressEvent(event)

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if not self._dragInProgress and self._pressedIndex != -1:
            if (event.pos() - self._dragStartPosition).manhattanLength() > QApplication.startDragDistance():
                self._dragInProgress = True

        super(TabBarHelper, self).mouseMoveEvent(event)

        # Hack to find QMovableTabWidget
        if self._dragInProgress and not self._movingTab:
            objects = self.children()
            taboverlap = self.style().pixelMetric(QStyle.PM_TabBarTabOverlap, None, self)
            grabRect = self.tabRect(self.currentIndex())
            grabRect.adjust(-taboverlap, 0, taboverlap, 0)
            for obj in objects:
                # TODO: QWidget *widget = qobject_cast<QWidget*>(object);
                widget = obj
                if widget and widget.geometry() == grabRect:
                    # m_movingTab = static_cast<QMovableTabWidget*>(widget)
                    self._movingTab = widget
                    break

        # Don't allow to move tabs outside of tabbar
        if self._dragInProgress and self._movingTab:
            # FIXME: This does't work at all with RTL...
            if self.isRightToLeft():
                return
            r = self.tabRect(self._pressedIndex)
            r.moveLeft(r.x() + (event.pos().x() - self._dragStartPosition.x()))
            sendEvent = False
            diff = r.topRight().x() - self.tabRect(self.count() - 1).topRight().x()
            if diff > 0:
                sendEvent = True
            else:
                diff = r.topLeft().x() - self.tabRect(0).topLeft().x()
                if diff < 0:
                    sendEvent = True
            if sendEvent:
                pos = event.pos()
                pos.setX(pos.x() - diff)
                ev = QMouseEvent(event.type(), pos, event.button(),
                    event.buttons(), event.modifiers())
                super(TabBarHelper, self).mouseMoveEvent(ev)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        event.ignore()

        if event.button() == Qt.LeftButton:
            self._pressedIndex = -1
            self._dragInProgress = False
            self._dragStartPosition = QPoint()

        super(TabBarHelper, self).mouseReleaseEvent(event)

        self.update()

    def _dragOffset(self, option, tabIndex):
        '''
        @param: option QStyleOptionTab
        @param: tabIndex int
        '''
        rect = QRect()
        button = self.tabButton(tabIndex, QTabBar.LeftSide)
        if button:
            rect = self.style().subElementRect(QStyle.SE_TabBarTabLeftButton, option, self)
        if not rect.isValid():
            button = self.tabButton(tabIndex, QTabBar.RightSide)
            rect = self.style().subElementRect(QStyle.SE_TabBarTabRightButton, option, self)
        if not button or not rect.isValid():
            return 0
        return button.pos().x() - rect.topLeft().x()

    def _initStyleOption(self, option, tabIndex):
        '''
        @param: option QStyleOptionTab
        @param: tabIndex int
        '''
        super(TabBarHelper, self).initStyleOption(option, tabIndex)

        # Workaround zero padding when tabs are styled using style sheets
        if self._tabPadding:
            textRect = self.style().subElementRect(QStyle.SE_TabBarTabText, option, self)
            width = textRect.width() - 2 * self._tabPadding
            option.text = option.fontMetrics.elidedText(
                self.tabText(tabIndex), self.elideMode(), width, Qt.TextShowMnemonic,
            )

class TabScrollBar(QScrollBar):
    def __init__(self, parent=None):
        super(TabScrollBar, self).__init__(parent)
        self._animation = QPropertyAnimation(self, b'value', self)  # QPropertyAnimation

    def isScrolling(self):
        return self._animation.state() == QPropertyAnimation.Running

    def animateToValue(self, to, type_=QEasingCurve.OutQuad):
        '''
        @param: to int
        @param: type_ QEasingCurve::Type
        '''
        to = max(self.minimum(), min(to, self.maximum()))
        length = abs(to - self.value())
        duration = min(1500, 200 + length / 2)

        self._animation.stop()
        self._animation.setEasingCurve(type_)
        self._animation.setDuration(duration)
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(to)
        self._animation.start()

class TabBarScrollWidget(QWidget):
    def __init__(self, tabBar, parent=None):
        '''
        @param: tabBar QTabBar
        '''
        super(TabBarScrollWidget, self).__init__(parent)
        self._tabBar = tabBar
        self._usesScrollButtons = False
        self._totalDeltas = 0

        self._scrollArea = QScrollArea(self)
        self._scrollArea.setFocusPolicy(Qt.NoFocus)
        self._scrollArea.setFrameStyle(QFrame.NoFrame)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._scrollBar = TabScrollBar(self._scrollArea)
        self._scrollArea.setHorizontalScrollBar(self._scrollBar)
        self._scrollArea.setWidget(self._tabBar)

        self._leftScrollButton = ToolButton(self)
        self._leftScrollButton.setFocusPolicy(Qt.NoFocus)
        self._leftScrollButton.setAutoRaise(True)
        self._leftScrollButton.setObjectName('tabbar-button-left')
        self._leftScrollButton.setAutoRepeat(True)
        self._leftScrollButton.setAutoRepeatDelay(200)
        self._leftScrollButton.setAutoRepeatInterval(200)
        self._leftScrollButton.pressed.connect(self._scrollStart)
        self._leftScrollButton.doubleClicked.connect(self.scrollToLeftEdge)
        self._leftScrollButton.middleMouseClicked.connect(self.ensureVisible)

        self._rightScrollButton = ToolButton(self)
        self._rightScrollButton.setFocusPolicy(Qt.NoFocus)
        self._rightScrollButton.setAutoRaise(True)
        self._rightScrollButton.setObjectName('tabbar-button-right')
        self._rightScrollButton.setAutoRepeat(True)
        self._rightScrollButton.setAutoRepeatDelay(200)
        self._rightScrollButton.setAutoRepeatInterval(200)
        self._rightScrollButton.pressed.connect(self._scrollStart)
        self._rightScrollButton.doubleClicked.connect(self.scrollToRightEdge)
        self._rightScrollButton.middleMouseClicked.connect(self.ensureVisible)

        hLayout = QHBoxLayout()
        hLayout.setSpacing(0)
        hLayout.setContentsMargins(0, 0, 0, 0)
        hLayout.addWidget(self._leftScrollButton)
        hLayout.addWidget(self._scrollArea)
        hLayout.addWidget(self._rightScrollButton)
        self.setLayout(hLayout)

        self._scrollArea.viewport().setAutoFillBackground(False)
        self._scrollBar.valueChanged.connect(self._updateScrollButtonsState)

        self._updateScrollButtonsState()
        self._overFlowChanged(False)

    def tabBar(self):
        '''
        @return: QTabBar
        '''
        return self._tabBar

    def scrollArea(self):
        '''
        @return: QScrollArea
        '''
        return self._scrollArea

    def scrollBar(self):
        '''
        @return: TabScrollBar
        '''
        return self._scrollBar

    def scrollByWheel(self, event):
        '''
        @param: event QWheelEvent
        '''
        event.accept()

        # Check if direction has changed from last time
        if self._totalDeltas * event.delta() < 0:
            self._totalDeltas = 0

        self._totalDeltas += event.delta()

        # Slower scrolling for horizontal wheel scrolling
        if event.orientation() == Qt.Horizontal:
            if event.delta() > 0:
                self.scrollToLeft()
            elif event.delta() < 0:
                self.scrollToRight()
            return

        # Faster scrolling with control modifier
        if event.orientation() == Qt.Vertical and event.modifiers() == Qt.ControlModifier:
            if event.delta() > 0:
                self.scrollToLeft(10)
            elif event.delta() < 0:
                self.scrollToRight(10)

            return

        # Fast scrolling with just wheel scroll
        factor = max(int(self._scrollBar.pageStep() / 1.5 + 0.5), self._scrollBar.singleStep())
        if (event.modifiers() & Qt.ControlModifier) or event.modifiers() & Qt.ShiftModifier:
            factor = self._scrollBar.pageStep()

        offset = (self._totalDeltas / 120) * factor
        if offset != 0:
            if self.isRightToLeft():
                self._scrollBar.animateToValue(self._scrollBar.value() + offset)
            else:
                self._scrollBar.animateToValue(self._scrollBar.value() - offset)

            self._totalDeltas -= (offset / factor) * 120

    def scrollButtonsWidth(self):
        # Assumes both buttons have the save width
        return self._leftScrollButton.width()

    def usesScrollButtons(self):
        '''
        @return: bool
        '''
        return self._usesScrollButtons

    def setUsesScrollButtons(self, useButtons):
        '''
        @param: useButtons  bool
        '''
        if useButtons != self._usesScrollButtons:
            self._usesScrollButtons = useButtons
            self._updateScrollButtonsState()
            self._tabBar.setElideMode(self._tabBar.elideMode())

    def isOverflowed(self):
        # TODO: ?
        return self._tabBar.count() > 0 and \
            self._scrollBar.minimum() != self._scrollBar.maximum()

    def tabAt(self, pos):
        '''
        @param: pos QPoint
        @return: int
        '''
        if self._leftScrollButton.isVisible() and \
            (self._leftScrollButton.rect().contains(pos) or
                self._rightScrollButton.rect().contains(pos)):
            return -1

        return self._tabBar.tabAt(self._tabBar.mapFromGlobal(self.mapToGlobal(pos)))

    # public Q_SLOTS:
    def ensureVisible(self, index=-1, xmargin=132):
        if index == -1:
            index = self._tabBar.currentIndex()

        if index < 0 or index >= self._tabBar.count():
            return
        xmargin = min(xmargin, self._scrollArea.viewport().width() / 2)

        # Qt But? the following lines were taken from QScollArea::ensureVisible()
        # and then were fixed. The original version caculates wrong value in RTL
        # layouts.
        logicalTabRect = QStyle.visualRect(self._tabBar.layoutDirection(),
            self._tabBar.rect(), self._tabBar.tabRect(index))
        logicalX = QStyle.visualPos(Qt.LeftToRight, self._scrollArea.viewport().rect(),
            logicalTabRect.center()).x()

        if logicalX - xmargin < self._scrollBar.value():
            self._scrollBar.animateToValue(max(0, logicalX - xmargin))
        elif logicalX > self._scrollBar.value() + self._scrollArea.viewport().width() - xmargin:
            self._scrollBar.animateToValue(min(
                logicalX - self._scrollArea.viewport().width() + xmargin,
                self._scrollBar.maximum()
            ))

    def scrollToLeft(self, n=5, type_=QEasingCurve.OutQuad):
        n = max(1, n)
        self._scrollBar.animateToValue(self._scrollBar.value() - n * self._scrollBar.singleStep(), type_)

    def scrollToRight(self, n=5, type_=QEasingCurve.OutQuad):
        n = max(1, n)
        self._scrollBar.animateToValue(self._scrollBar.value() + n * self._scrollBar.singleStep(), type_)

    def scrollToLeftEdge(self):
        self._scrollBar.animateToValue(self._scrollBar.minimum())

    def scrollToRightEdge(self):
        self._scrollBar.animateToValue(self._scrollBar.maximum())

    def setUpLayout(self):
        height = self._tabBar.height()

        self.setFixedHeight(height)

    # private Q_SLOTS:
    def _overFlowChanged(self, overflowed):
        showScrollButtons = overflowed and self._usesScrollButtons

        self._leftScrollButton.setVisible(showScrollButtons)
        self._rightScrollButton.setVisible(showScrollButtons)

    def _scrollStart(self):
        ctrlModifier = QApplication.keyboardModifiers() & Qt.ControlModifier

        if self.sender() == self._leftScrollButton:
            if ctrlModifier:
                self.scrollToLeftEdge()
            else:
                self.scrollToLeft(5, QEasingCurve.Linear)
        elif self.sender() == self._rightScrollButton:
            if ctrlModifier:
                self.scrollToRightEdge()
            else:
                self.scrollToRight(5, QEasingCurve.Linear)

    def _updateScrollButtonsState(self):
        self._leftScrollButton.setEnabled(self._scrollBar.value() != self._scrollBar.minimum())
        self._rightScrollButton.setEnabled(self._scrollBar.value() != self._scrollBar.maximum())

    # private:
    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        event.ignore()

    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super(TabBarScrollWidget, self).resizeEvent(event)

        self._updateScrollButtonsState()

# donot use firstly
class CloseButton(QAbstractButton):
    '''
    @brief: Class from close button on tabs
        * taken from qtabbar.cpp
    '''
    def __init__(self, parent=None):
        super(CloseButton, self).__init__(parent)
        self.setObjectName('combotabbar_tabs_close_button')
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        self.resize(self.sizeHint())

    # override
    def sizeHint(self):
        '''
        @return: QSize
        '''
        self.ensurePolished()
        width = self.style().pixelMetric(QStyle.PM_TabCloseIndicatorWidth)
        height = self.style().pixelMetric(QStyle.PM_TabCloseIndicatorHeight)
        return QSize(width, height)

    # override
    def enterEvent(self, event):
        '''
        @param: event QEvent
        '''
        if self.isEnabled():
            self.update()
        super(CloseButton, self).enterEvent(event)

    # override
    def leaveEvent(self, event):
        '''
        @param: event QEvent
        '''
        if self.isEnabled():
            self.update()

        super(CloseButton, self).leaveEvent(event)

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        p = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        opt.state |= QStyle.State_AutoRaise

        # update raised state on scrolling
        isUnderMouse = self.rect().contains(self.mapFromGlobal(QCursor.pos()))

        if self.isEnabled() and isUnderMouse and not self.isChecked() and not self.isDown():
            opt.state |= QStyle.State_Raised
        if self.isChecked():
            opt.state |= QStyle.State_On
        if self.isDown():
            opt.state |= QStyle.State_Sunken

        # tb TabBarhelper
        tb = self.parent()
        if tb:
            index = tb.currentIndex()
            # closeSide QTabBar::ButtonPosition
            closeSide = self.style().styleHint(QStyle.SH_TabBar_CloseButtonPosition)
            if tb.tabButton(index, closeSide) == self and tb.isActiveTabBar():
                opt.state |= QStyle.State_Selected

        self.style().drawPrimitive(QStyle.PE_IndicatorTabClose, opt, p, self)

class ComboTabBar(QWidget):
    # SizeType
    PinnedTabWidth = 0
    ActiveTabMinimumWidth = 1
    NormalTabMinimumWidth = 2
    NormalTabMaximumWidth = 3
    OverflowedTabWidth = 4
    ExtraReservedWidth = 5

    # DropIndicatorPosition
    BeforTab = 0
    AfterTab = 1

    def __init__(self, parent=None):
        super(ComboTabBar, self).__init__(parent)
        self._mainLayout = None
        self._leftLayout = None
        self._rightLayout = None
        self._leftContainer = None
        self._rightContainer = None

        self._mainTabBar = None
        self._pinnedTabBar = None

        self._mainTabBarWidget = None
        self._pinnedTabBarWidget = None

        self._closeButtonsToolTip = ''
        self._mainBarOverFlowed = False
        self._lastAppliedOverflow = False
        self._usesScrollButtons = False
        self._blockCurrentChangedSignal = False

        self._wheelHelper = WheelHelper()

        # init
        super(ComboTabBar, self).setObjectName('tabbarwidget')

        self._mainTabBar = TabBarHelper(isPinnedTabBar=False, comboTabBar=self)
        self._pinnedTabBar = TabBarHelper(isPinnedTabBar=True, comboTabBar=self)
        self._mainTabBarWidget = TabBarScrollWidget(self._mainTabBar, self)
        self._pinnedTabBarWidget = TabBarScrollWidget(self._pinnedTabBar, self)

        self._mainTabBar.setScrollArea(self._mainTabBarWidget.scrollArea())
        self._pinnedTabBar.setScrollArea(self._pinnedTabBarWidget.scrollArea())

        self._mainTabBarWidget.scrollBar().rangeChanged.connect(self._setMinimumWidths)
        self._mainTabBarWidget.scrollBar().valueChanged.connect(self.scrollBarValueChanged)
        self._pinnedTabBarWidget.scrollBar().rangeChanged.connect(self._setMinimumWidths)
        self._pinnedTabBarWidget.scrollBar().valueChanged.connect(self.scrollBarValueChanged)
        self.overFlowChanged.connect(self._mainTabBarWidget._overFlowChanged)

        self._mainTabBar.setActiveTabBar(True)
        self._pinnedTabBar.setActiveTabBar(False)

        self._leftLayout = QHBoxLayout()
        self._leftLayout.setSpacing(0)
        self._leftLayout.setContentsMargins(0, 0, 0, 0)
        self._leftContainer = QWidget(self)
        self._leftContainer.setLayout(self._leftLayout)
        self._leftContainer.setStyleSheet('background-color: blue')

        self._rightLayout = QHBoxLayout()
        self._rightLayout.setSpacing(0)
        self._rightLayout.setContentsMargins(0, 0, 0, 0)
        self._rightContainer = QWidget(self)
        self._rightContainer.setLayout(self._rightLayout)
        self._rightContainer.setStyleSheet('background-color: red')

        self._mainLayout = QHBoxLayout()
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.addWidget(self._leftContainer)
        self._mainLayout.addWidget(self._pinnedTabBarWidget)
        self._mainLayout.addWidget(self._mainTabBarWidget)
        self._mainLayout.addWidget(self._rightContainer)
        self.setLayout(self._mainLayout)

        self._mainTabBar.currentChanged.connect(self._slotCurrentChanged)
        self._mainTabBar.tabCloseRequested.connect(self._slotTabCloseRequested)
        self._mainTabBar.tabMoved.connect(self._slotTabMoved)

        self._pinnedTabBar.currentChanged.connect(self._slotCurrentChanged)
        self._pinnedTabBar.tabCloseRequested.connect(self._slotTabCloseRequested)
        self._pinnedTabBar.tabMoved.connect(self._slotTabMoved)

        self.setAutoFillBackground(False)
        self._mainTabBar.setAutoFillBackground(False)
        self._pinnedTabBar.setAutoFillBackground(False)

        self._mainTabBar.installEventFilter(self)
        self._pinnedTabBar.installEventFilter(self)
        self._leftContainer.installEventFilter(self)
        self._rightContainer.installEventFilter(self)
        self._mainTabBarWidget.installEventFilter(self)
        self._pinnedTabBarWidget.installEventFilter(self)

    def addTabByText(self, text):
        return self.insertTabByText(-1, text)

    def addTabByIconText(self, icon, text):
        return self.insertTabByIconText(-1, icon, text)

    def insertTabByText(self, index, text):
        return self.insertTabByIconText(index, QIcon(), text)

    def insertTabByIconText(self, index, icon, text, pinned=False):
        if pinned:
            index = self._pinnedTabBar.insertTab(index, icon, text)
        else:
            index = self._mainTabBar.insertTab(index - self.pinnedTabsCount(), icon, text)

            # TODO: enbale close button later
            #if self.tabsCloseable():
            #    closeButton = self._mainTabBar.tabButton(index, self.closeButtonPosition())
            #    if closeButton and closeButton.objectName() != 'combotabbar_tabs_close_button':
            #        # insert our close button
            #        self.insertCloseButton(index+self.pinnedTabsCount())
            #        if closeButton:
            #            closeButton.deleteLater()

            index += self.pinnedTabsCount()

        self._updatePinnedTabBarVisibility()
        self._tabInserted(index)
        self._setMinimumWidths()

        return index

    def removeTab(self, index):
        if self.validIndex(index):
            self.setUpdatesEnabled(False)

            self._localTabBar(index).removeTab(self._toLocalIndex(index))
            self._updatePinnedTabBarVisibility()
            self._tabRemoved(index)
            self._setMinimumWidths()

            self.setUpdatesEnabled(True)
            self._updateTabBars()

    def moveTab(self, from_, to_):
        if from_ >= self.pinnedTabsCount() and to_ >= self.pinnedTabsCount():
            self._mainTabBar.moveTab(from_-self.pinnedTabsCount(), to_-self.pinnedTabsCount())
        elif from_ < self.pinnedTabsCount() and to_ < self.pinnedTabsCount():
            self._pinnedTabBar.moveTab(from_, to_)

    def isTabEnabled(self, index):
        return self._localTabBar(index).isTabEnabled(self._toLocalIndex(index))

    def setTabEnabled(self, index, enabled):
        self._localTabBar(index).setTabEnabled(self._toLocalIndex(index), enabled)

    def tabTextColor(self, index):
        return self._localTabBar(index).tabTextColor(self._toLocalIndex(index))

    def setTabTextColor(self, index, color):
        self._localTabBar(index).setTabTextColor(self._toLocalIndex(index), color)

    def tabRect(self, index):
        '''
        @return: QRect
        '''
        lTabBar = self._localTabBar(index)
        return self._mapFromLocalTabRect(lTabBar.tabRect(self._toLocalIndex(index)), lTabBar)

    def draggedTabRect(self):
        '''
        @return: QRect
        '''
        rect = self._pinnedTabBar.draggedTabRect()
        if rect.isValid():
            return self._mapFromLocalTabRect(rect, self._pinnedTabBar)
        return self._mapFromLocalTabRect(self._mainTabBar.draggedTabRect(), self._mainTabBar)

    def tabPixmap(self, index):
        '''
        @return: QPixmap
        '''
        self._localTabBar(index).tabPixmap(self._toLocalIndex(index))

    def tabAt(self, pos):
        '''
        @brief: Returns tab index at pos, or -1
        @param: pos QPoint
        '''
        w = QApplication.widgetAt(self.mapToGlobal(pos))
        if not isinstance(w, TabBarHelper) and not isinstance(w, TabIcon) and \
                not isinstance(w, CloseButton):
            return

        if self._pinnedTabBarWidget.geometry().contains(pos):
            return self._pinnedTabBarWidget.tabAt(self._pinnedTabBarWidget.mapFromParent(pos))
        elif self._mainTabBarWidget.geometry().contains(pos):
            index = self._mainTabBarWidget.tabAt(self._mainTabBarWidget.mapFromParent(pos))
            if index != -1:
                index += self.pinnedTabsCount()
            return index

        return -1

    def emptyArea(self, pos):
        '''
        @brief: Returns true if there is an empty area at pos
            returns false if there are buttons or other widgets on the pos
        @param: pos QPoint
        '''
        if self.tabAt(pos) != -1:
            return False

        helper = QApplication.widgetAt(self.mapToGlobal(pos))
        return isinstance(helper, TabBarHelper)

    def mainTabBarCurrentIndex(self):
        if self._mainTabBar.currentIndex() == -1:
            return -1
        else:
            return self.pinnedTabsCount() + self._mainTabBar.currentIndex()

    def currentIndex(self):
        if self._pinnedTabBar.isActiveTabBar():
            return self._pinnedTabBar.currentIndex()
        else:
            if self._mainTabBar.currentIndex() == -1:
                return -1
            else:
                return self.pinnedTabsCount() + self._mainTabBar.currentIndex()

    def count(self):
        return self.pinnedTabsCount() + self._mainTabBar.count()

    def setDrawBase(self, drawTheBase):
        self._mainTabBar.setDrawBase(drawTheBase)
        self._pinnedTabBar.setDrawBase(drawTheBase)

    def drawBase(self):
        return self._mainTabBar.drawBase()

    def elideMode(self):
        '''
        @return: Qt:TextElideMode
        '''
        return self._mainTabBar.elideMode()

    def setElideMode(self, elide):
        '''
        @param: elide Qt::TextElideMode
        '''
        self._mainTabBar.setElideMode(elide)
        self._pinnedTabBar.setElideMode(elide)

    def tabText(self, index):
        '''
        @return: QString
        '''
        self._localTabBar(index).tabText(self._toLocalIndex(index))

    def setTabText(self, index, text):
        self._localTabBar(index).setTabText(self._toLocalIndex(index), text)

    def tabToolTip(self, index):
        '''
        @return: QString
        '''
        return self._localTabBar(index).tabToolTip(self._toLocalIndex(index))

    def setTabToolTip(self, index, tip):
        '''
        @param: tip QString
        '''
        self._localTabBar(index).setTabToolTip(self._toLocalIndex(index), tip)

    def tabsCloseable(self):
        return self._mainTabBar.tabsClosable()

    def setTabsCloseable(self, closable):
        if closable == self.tabsCloseable():
            return

        if closable:
            # insert our close button
            for idx in range(self._mainTabBar.count()):
                closeButton = self._mainTabBar.tabButton(idx, self.closeButtonPosition())
                if closeButton:
                    if closeButton.objectName() == 'combotabbar_tabs_close_button':
                        continue

                self.insertCloseButton(idx + self.pinnedTabsCount())
                if closeButton:
                    closeButton.deleteLater()

        self._mainTabBar.setTabsClosable(closable)

    def tabButton(self, index, position):
        '''
        @param: position QTabBar::ButtonPosition
        @return: QWidget
        '''
        return self._localTabBar(index).tabButton(
            self._toLocalIndex(index), position,
        )

    def setTabButton(self, index, position, widget):
        '''
        @param: position QTabBar::ButtonPosition
        @param: widget QWidget
        '''
        if widget:
            widget.setMinimumSize(self.closeButtonSize())
        self._localTabBar(index).setTabButton(
            self._toLocalIndex(index), position, widget
        )

    def selectionBehaviorOnRemove(self):
        '''
        @return: QTabBar::SelectionBehavior
        '''
        return self._mainTabBar.selectionBehaviorOnRemove()

    def setSelectionBehaviorOnRemove(self, behavior):
        '''
        @param: QTabBar::selectionBehavior
        '''
        self._mainTabBar.setSelectionBehaviorOnRemove(behavior)
        self._pinnedTabBar.setSelectionBehaviorOnRemove(behavior)

    def expanding(self):
        '''
        @return: bool
        '''
        return self._mainTabBar.expanding()

    def setExpanding(self, enabled):
        self._mainTabBar.setExpanding(enabled)
        self._pinnedTabBar.setExpanding(enabled)

    def isMovable(self):
        return self._mainTabBar.isMovable()

    def setMovable(self, movable):
        self._mainTabBar.setMovable(movable)
        self._pinnedTabBar.setMovable(movable)

    def documentMode(self):
        '''
        @return: bool
        '''
        return self._mainTabBar.documentMode()

    def setDocumentModel(self, set_):
        self._mainTabBar.setDocumentMode(set_)
        self._pinnedTabBar.setDocumentMode(set_)

    def pinnedTabsCount(self):
        return self._pinnedTabBar.count()

    def normalTabsCount(self):
        return self._mainTabBar.count()

    def isPinned(self, index):
        return self.index >= 0 and index < self.pinnedTabsCount()

    def setFocusPolicy(self, policy):
        '''
        @param: policy Qt::FocusPolicy
        '''
        super(ComboTabBar, self).setFocusPolicy(policy)
        self._mainTabBar.setFocusPolicy(policy)
        self._pinnedTabBar.setFocusPolicy(policy)

    def setObjectName(self, name):
        '''
        @param: name QString
        '''
        self._mainTabBar.setObjectName(name)
        self._pinnedTabBar.setObjectName(name)

    def setMouseTracking(self, enable):
        self._mainTabBarWidget.scrollArea().setMouseTracking(enable)
        self._mainTabBarWidget.setMouseTracking(enable)
        self._mainTabBar.setMouseTracking(enable)

        self._pinnedTabBarWidget.scrollArea().setMouseTracking(enable)
        self._pinnedTabBarWidget.setMouseTracking(enable)
        self._pinnedTabBar.setMouseTracking(enable)

        super(ComboTabBar, self).setMouseTracking(enable)

    def insertCloseButton(self, index):
        index -= self.pinnedTabsCount()
        if index < 0:
            return

        closeButton = CloseButton(self)
        closeButton.setFixedSize(self.closeButtonSize())
        closeButton.setToolTip(self._closeButtonsToolTip)
        closeButton.clicked.connect(self._closeTabFromButton)
        self._mainTabBar.setTabButton(index, self.closeButtonPosition(), closeButton)

    def setCloseButtonsToolTip(self, tip):
        self._closeButtonsToolTip = tip

    def iconButtonPosition(self):
        '''
        @return: QTabBar::ButtonPosition
        '''
        if self.closeButtonPosition() == QTabBar.RightSide:
            return QTabBar.LeftSide
        else:
            return QTabBar.RightSide

    def closeButtonPosition(self):
        '''
        @return: QTabBar::ButtonPosition
        '''
        result = self.style().styleHint(
            QStyle.SH_TabBar_CloseButtonPosition,
            None, self._mainTabBar)
        # TODO: convert result to QTabBar::ButtonPosition
        return result

    def iconButtonSize(self):
        '''
        @return: QSize
        '''
        s = self.closeButtonSize()
        s.setWidth(max(16, s.width()))
        s.setHeight(max(16, s.height()))
        return s

    def closeButtonSize(self):
        '''
        @return: QSize
        '''
        width = self.style().pixelMetric(QStyle.PM_TabCloseIndicatorWidth, None, self)
        height = self.style().pixelMetric(QStyle.PM_TabCloseIndicatorHeight, None, self)
        return QSize(width, height)

    def validIndex(self, index):
        return index >= 0 and index < self.count()

    def setCurrentNextEnabledIndex(self, offset):
        index = self.currentIndex() + offset
        while self.validIndex(index):
            if self.isTabEnabled(index):
                self.setCurrentIndex(index)
                break
            index += offset

    def usesScrollButtons(self):
        '''
        @return: bool
        '''
        return self._mainTabBar.usesScrollButtons()

    def setUsesScrollButtons(self, useButtons):
        '''
        @param: useButtons bool
        '''
        self._mainTabBarWidget.setUsesScrollButtons(useButtons)

    def showDropIndicator(self, index, position):
        '''
        @param: position DropIndicatorPosition
        '''
        self.clearDropIndicator()
        self._localTabBar(index).showDropIndicator(self._toLocalIndex(index), position)

    def clearDropIndicator(self):
        self._mainTabBar.clearDropIndicator()
        self._pinnedTabBar.clearDropIndicator()

    def isDragInProgress(self):
        return self._mainTabBar.isDragInProgress() or \
            self._pinnedTabBar.isDragInProgress()

    def isScrollInProcess(self):
        return self._mainTabBarWidget.scrollBar().isScrolling() or \
            self._pinnedTabBarWidget.scrollBar().isScrolling()

    def isMainBarOverflowed(self):
        return self._mainBarOverFlowed

    def cornerWidth(self, corner):
        '''
        @brief: Width of all widgets in the corner
        '''
        if corner == Qt.TopLeftCorner:
            return self._leftContainer.width()
        elif corner == Qt.TopRightCorner:
            return self._rightContainer.width()

        raise RuntimeError('ComboTabBar::cornerWidth Only TopLeft and TopRight corners ar implemented!')
        return -1

    def addCornerWidget(self, widget, corner):
        '''
        @brief: Add widget to the left/right corner
        @param: widget QWidget
        @param: corner Qt::Corner
        '''
        if corner == Qt.TopLeftCorner:
            self._leftLayout.addWidget(widget)
        elif corner == Qt.TopRightCorner:
            self._rightLayout.addWidget(widget)
        else:
            raise RuntimeError('ComboTabBar::addCornerWidth Only TopLeft and TopRight conners are implemented!')

    @staticmethod
    def slideAnimationDuration(cls):
        '''
        @note: taken from qtabbar_p.h
        @return: int
        '''
        return 250

    # Q_SLOTS
    def setUpLayout(self):
        height = max(self._mainTabBar.height(), self._pinnedTabBar.height())

        if height < 1:
            height = max(self._mainTabBar.sizeHint().height(), self._pinnedTabBar.sizeHint().height())

        # We need to setup heights even before m_mainTabBar->height() has
        # correct value. So lets just set minimum 5px height
        height = max(5, height)

        self.setFixedHeight(height)
        self._leftContainer.setFixedHeight(height)
        self._rightContainer.setFixedHeight(height)
        self._mainTabBarWidget.setUpLayout()
        self._pinnedTabBarWidget.setUpLayout()

        self._setMinimumWidths()

        if self.isVisible() and height > 5:
            # ComboTabBar is now visible, we can sync heights of both tabbars
            self._mainTabBar.setFixedHeight(height)
            self._pinnedTabBar.setFixedHeight(height)

    def ensureVisible(self, index=-1, xmargin=-1):
        if index == -1:
            index = self.currentIndex()

        if index < self.pinnedTabsCount():
            if xmargin == -1:
                xmargin = max(20, self._comboTabBarPixelMetric(self.PinnedTabWidth))
            self._pinnedTabBarWidget.ensureVisible(index, xmargin)
        else:
            if xmargin == -1:
                xmargin = self._comboTabBarPixelMetric(self.OverflowedTabWidth)
            index -= self.pinnedTabsCount()
            self._mainTabBarWidget.ensureVisible(index, xmargin)

    def setCurrentIndex(self, index):
        self._localTabBar(index).setCurrentIndex(self._toLocalIndex(index))

    # properties
    # currentIndex = pyqtProperty(int, currentIndex, setCurrentIndex)
    # count = pyqtProperty(int, count)

    # Q_SIGNALS
    overFlowChanged = pyqtSignal(bool) # overFlow
    currentChanged = pyqtSignal(int)  # index
    tabCloseRequested = pyqtSignal(int) # index
    tabMoved = pyqtSignal(int, int) # from, to
    scrollBarValueChanged = pyqtSignal(int) # value

    # private Q_SLOTS:
    def _setMinimumWidths(self):
        if self.isVisible() or self._comboTabBarPixelMetric(self.PinnedTabWidth) < 0:
            return

        tabBarsSpacing = 3  # to distinguish tabbars
        pinnedTabBarWidth = self.pinnedTabsCount() * self._comboTabBarPixelMetric(ComboTabBar.PinnedTabWidth)
        self._pinnedTabBar.setMinimumWidth(pinnedTabBarWidth)
        self._pinnedTabBarWidget.setFixedWidth(pinnedTabBarWidth + tabBarsSpacing)

        # Width that is needed by main tabbar
        mainTabBarWidth = self._comboTabBarPixelMetric(self.NormalTabMinimumWidth) * \
            (self._mainTabBar.count() - 1) + \
            self._comboTabBarPixelMetric(self.ActiveTabMinimumWidth) + \
            self._comboTabBarPixelMetric(self.ExtraReservedWidth)

        # This is the full width that would be needed for the tabbar (including
        # pinnned tabbar and corner widgets)
        realTabBarWidth = mainTabBarWidth + self._pinnedTabBarWidget.width() + \
            self.cornerWidth(Qt.TopLeftCorner) + \
            self.cornerWidth(Qt.TopRightCorner)

        # Does it fit in our widget?
        if realTabBarWidth <= self.width():
            if self._mainBarOverFlowed:
                self._mainBarOverFlowed = False
                QTimer.singleShot(0, self._emitOverFlowChanged)

            self._mainTabBar.useFastTabSizeHint(False)
            self._mainTabBar.setMinimumWidth(mainTabBarWidth)
        else:
            if self._mainBarOverFlowed:
                self._mainBarOverFlowed = True
                QTimer.singleShot(0, self._emitOverFlowChanged)

            # All tabs have now same width, we can use fast tabSizeHint
            self._mainTabBar.useFastTabSizeHint(True)
            self._mainTabBar.setMinimumWidth(self._mainTabBar.count() *
                self._comboTabBarPixelMetric(self.OverflowedTabWidth))

    def _slotCurrentChanged(self, index):
        if self._blockCurrentChangedSignal:
            return

        if self.sender() == self._pinnedTabBar:
            if index == -1 and self._mainTabBar.count() > 0:
                self._mainTabBar.setActiveTabBar(True)
                self._pinnedTabBar.setActiveTabBar(False)
                self.currentChanged.emit(self.pinnedTabsCount())
            else:
                self._pinnedTabBar.setActiveTabBar(True)
                self._mainTabBar.setActiveTabBar(False)
                self.currentChanged.emit(index)

        else:
            if index == -1 and self.pinnedTabsCount() > 0:
                self._pinnedTabBar.setActiveTabBar(True)
                self._mainTabBar.setActiveTabBar(False)
                self.currentChanged.emit(self.pinnedTabsCount() - 1)
            else:
                self._mainTabBar.setActiveTabBar(True)
                self._pinnedTabBar.setActiveTabBar(False)
                self.currentChanged.emit(index+self.pinnedTabsCount())

    def _slotTabCloseRequested(self, index):
        if self.sender() == self._pinnedTabBar:
            self.tabCloseRequested.emit(index)
        else:
            self.tabCloseRequested.emit(index+self.pinnedTabsCount())

    def _slotTabMoved(self, from_, to_):
        if self.sender() == self._pinnedTabBar:
            self.tabMoved.emit(from_, to_)
        else:
            self.tabMoved.emit(from_+self.pinnedTabsCount(),
                to_+self.pinnedTabsCount())

    def _closeTabFromButton(self):
        # TODO: QWidget* button = qobject_cast<QWidget*>(sender());
        button = self.sender()

        tabToClose = -1

        for idx in range(self._mainTabBar.count()):
            if self._mainTabBar.tabButton(idx, self.closeButtonPosition()) == button:
                tabToClose = idx
                break

        if tabToClose != -1:
            self.tabCloseRequested.emit(tabToClose + self.pinnedTabsCount())

    def _updateTabBars(self):
        self._mainTabBar.update()
        self._pinnedTabBar.update()

    def _emitOverFlowChanged(self):
        if self._mainBarOverFlowed != self._lastAppliedOverflow:
            self.overFlowChanged.emit(self._mainBarOverFlowed)
            self._lastAppliedOverflow = self._mainBarOverFlowed

    # protected:
    def _mainTabBarWidth(self):
        return self._mainTabBar.width()

    def _pinTabBarWidth(self):
        if self._pinnedTabBarWidget.isHidden():
            return 0
        else:
            return self._pinnedTabBarWidget.width()

    # override
    def event(self, event):
        '''
        @param: event QEvent
        @return: bool
        '''
        # bool
        res = super(ComboTabBar, self).event(event)

        evType = event.type()
        if evType == QEvent.ToolTip:
            if not self.isDragInProgress() and not self.isScrollInProcess():
                index = self.tabAt(self.mapFromGlobal(QCursor.pos()))
                if index >= 0:
                    QToolTip.showText(QCursor.pos(), self.tabToolTip(index))
        elif evType == QEvent.Resize:
            self.ensureVisible()
        elif evType == QEvent.Show:
            if not event.spontaneous():
                QTimer.singleShot(0, self.setUpLayout)
        elif evType in (QEvent.Enter, QEvent.Leave):
            # Make sure tabs are painted with correct mouseover state
            QTimer.singleShot(100, self._updateTabBars)

        return res

    # override
    def wheelEvent(self, event):
        '''
        @param: event QWheelEvent
        '''
        event.accept()

        if gVar.appSettings.alwaysSwitchTabsWithWheel or \
            (not self._mainTabBarWidget.isOverflowed() and
                not self._pinnedTabBarWidget.isOverflowed()):
            self._wheelHelper.processEvent(event)
            direction = self._wheelHelper.takeDirection()
            while direction:
                if direction in (WheelHelper.WheelUp, WheelHelper.WheelLeft):
                    self.setCurrentNextEnabledIndex(-1)
                    break
                elif direction in (WheelHelper.WheelDown, WheelHelper.WheelRight):
                    self.setCurrentNextEnabledIndex(1)
                    break
                else:
                    break
            return

        if self._mainTabBarWidget.underMouse():
            if self._mainTabBarWidget.isOverflowed():
                self._mainTabBarWidget.scrollByWheel(event)
            elif self._pinnedTabBarWidget.isOverflowed():
                self._pinnedTabBarWidget.scrollByWheel(event)
        elif self._pinnedTabBarWidget.underMouse():
            if self._pinnedTabBarWidget.isOverflowed():
                self._pinnedTabBarWidget.scrollByWheel(event)
            elif self._mainTabBarWidget.isOverflowed():
                self._mainTabBarWidget.scrollByWheel(event)

    # override
    def eventFilter(self, obj, ev):
        '''
        @param: obj QObject
        @param: ev QEvent
        '''
        if obj == self._mainTabBar and ev.type() == QEvent.Resize:
            # TODO: static_cast<QResizeEvent>(ev)
            event = ev
            if event.oldSize().height() != event.size().height():
                self.setUpLayout()

        # Hanlde wheel events exclusively in ComboTabBar
        if ev.type() == QEvent.Wheel:
            # TODO: static_cast<QWheelEvent>
            self.wheelEvent(ev)
            return True

        return super(ComboTabBar, self).eventFilter(obj, ev)

    # override
    def paintEvent(self, ev):
        '''
        @param: QPaintEvent
        '''
        # This is needed to apply style sheets
        option = QStyleOption()
        option.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, p, self)

        # macos? logic not implemented yet.

    def _comboTabBarPixelMetric(self, sizeType):
        '''
        @param: sizeType SizeType
        '''
        if sizeType == self.ExtraReservedWidth:
            return 0
        elif sizeType == self.NormalTabMaximumWidth:
            return 150
        elif sizeType in (
            self.ActiveTabMinimumWidth,
            self.NormalTabMinimumWidth,
            self.OverflowedTabWidth,
        ):
            return 100
        elif sizeType == self.PinnedTabWidth:
            return 30
        else:
            return -1

    def tabSizeHint(self, index, fast=False):
        '''
        @param: fast bool
        @return: QSize
        '''
        return self._localTabBar(index).baseClassTabSizeHint(
            self._toLocalIndex(index)
        )

    def _tabInserted(self, index):
        pass

    def _tabRemoved(self, index):
        pass

    def mainTabBar(self):
        return self._mainTabBar

    # private
    def _localTabBar(self, index=-1):
        if index < 0 or index >= self.pinnedTabsCount():
            return self._mainTabBar
        else:
            return self._pinnedTabBar

    def _toLocalIndex(self, globalIndex):
        if globalIndex < 0:
            return -1

        if globalIndex >= self.pinnedTabsCount():
            return globalIndex - self.pinnedTabsCount()
        else:
            return globalIndex

    def _mapFromLocalTabRect(self, rect, tabBar):
        '''
        @param: rect QRect
        @param: tabBar QWidget
        @return: QRect
        '''
        if not rect.isValid():
            return rect

        r = QRect()

        if tabBar == self._mainTabBar:
            r.moveLeft(r.x() + self.mapFromGlobal(self._mainTabBar.mapToGlobal(QPoint(0, 0))).x())
            widgetRect = self._mainTabBarWidget.scrollArea().viewport().rect()
            widgetRect.moveLeft(widgetRect.x() + self.mapFromGlobal(
                self._mainTabBarWidget.scrollArea().viewport().mapToGlobal(QPoint(0, 0))
            ).x())
            r = r.intersected(widgetRect)
        else:
            r.moveLeft(r.x() + self.mapFromGlobal(self._pinnedTabBar.mapToGlobal(QPoint(0, 0))).x())
            widgetRect = self._pinnedTabBarWidget.scrollArea().viewport().rect()
            widgetRect.moveLeft(widgetRect.x() + self.mapFromGlobal(
                self._pinnedTabBarWidget.scrollArea().viewport().mapToGlobal(QPoint(0, 0))
            ).x())
            r = r.intersected(widgetRect)

        return r

    def _updatePinnedTabBarVisibility(self):
        self._pinnedTabBarWidget.setVisible(self.pinnedTabsCount() > 0)
