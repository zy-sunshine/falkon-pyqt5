from .ComboTabBar import ComboTabBar
from .ComboTabBar import CloseButton
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QPoint
from mc.app.Settings import Settings
from PyQt5.Qt import QTabBar
from PyQt5.Qt import QSize
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from mc.common.globalvars import gVar
from PyQt5.QtWidgets import QLabel
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QTimer
from PyQt5.Qt import QStyle
from .TabContextMenu import TabContextMenu
from mc.common import const
from PyQt5.Qt import QMouseEvent
from PyQt5.Qt import QEvent
from PyQt5.Qt import QDrag
from PyQt5.Qt import QMimeData
from PyQt5.Qt import QUrl
from mc.webtab.WebTab import WebTab

class TabBarTabMetrics(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._metrics = {}  # QHash<int, int>

    def init(self):
        if self._metrics:
            return
        self._metrics[0] = 250
        self._metrics[1] = 100
        self._metrics[2] = 100
        self._metrics[3] = 100
        self._metrics[4] = -1  # Will be initialized from TabBar

    def normalMaxWidth(self):
        return self._metrics[0]

    def setNormalMaxWidth(self, value):
        self._metrics[0] = value

    def normalMinWidth(self):
        return self._metrics[1]

    def setNormalMinWidth(self, value):
        self._metrics[1] = value

    def activeMinWidth(self):
        return self._metrics[2]

    def setActiveMinWidth(self, value):
        self._metrics[2] = value

    def overflowedWidth(self):
        return self._metrics[3]

    def setOverflowedWidth(self, value):
        self._metrics[3] = value

    def pinnedWidth(self):
        return self._metrics[4]

    def setPinnedWidth(self, value):
        self._metrics[4] = value

class TabBar(ComboTabBar):
    _s_tabMetrics = None
    MIMETYPE = 'application/app.tabbar.tab'

    @classmethod
    def tabMetrics(cls):
        if not cls._s_tabMetrics:
            cls._s_tabMetrics = TabBarTabMetrics()
        return cls._s_tabMetrics

    def __init__(self, window, tabWidget):
        '''
        @param: window BrowserWindow
        @param: tabWidget TabWidget
        '''
        super(TabBar, self).__init__()
        self._window = window
        self._tabWidget = tabWidget
        self._hideTabBarWithOneTab = False
        self._showCloseOnInactive = False
        self._normalTabWidth = 0
        self._activeTabWidth = 0
        self._dragStartPosition = QPoint()  # QPoint
        self._forceHidden = False
        self._lastTab = None  # QPointer<WebTab>

        self.setObjectName('tabbar')
        self.setElideMode(Qt.ElideRight)
        self.setFocusPolicy(Qt.NoFocus)
        self.setTabsCloseable(False)
        self.setMouseTracking(True)
        self.setDocumentModel(True)
        self.setAcceptDrops(True)
        self.setDrawBase(False)
        self.setMovable(True)

        self.currentChanged.connect(self._currentTabChanged)

        # ComboTabBar features
        self.setUsesScrollButtons(True)
        self.setCloseButtonsToolTip(_('Close Tab'))
        self.overFlowChanged.connect(self._overflowChanged)

        self.tabMetrics().init()

        if gVar.app.isPrivate():
            privateBrowsing = QLabel(self)
            privateBrowsing.setObjectName('private-browsing-icon')
            privateBrowsing.setPixmap(IconProvider.privateBrowsingIcon().pixmap(16))
            privateBrowsing.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            privateBrowsing.setFixedWidth(30)
            self.addCornerWidget(privateBrowsing, Qt.TopLeftCorner)

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Browser-Tabs-Settings')
        self._hideTabBarWithOneTab = settings.value('hideTabsWithOneTab', False, type=bool)
        activateLastTab = settings.value('ActivateLastTabWhenCloseActual', False, type=bool)
        self._showCloseOnInactive = settings.value('showCloseOnInactiveTabs', 0, type=int)
        settings.endGroup()

        self.setSelectionBehaviorOnRemove(
            activateLastTab and QTabBar.SelectPreviousTab or QTabBar.SelectRightTab
        )
        self.setVisible(not (self.count() <= 1 and self._hideTabBarWithOneTab))

        self.setUpLayout()

    def tabWidget(self):
        return self._tabWidget

    # override
    def setVisible(self, visible):
        if self._forceHidden:
            super(TabBar, self).setVisible(False)
            return

        # Make sure to honor use preference
        if visible:
            visible = not (self.count() <= 1 and self._hideTabBarWithOneTab)

        super(TabBar, self).setVisible(visible)

    def setForceHidden(self, hidden):
        self._forceHidden = hidden
        self.setVisible(not self._forceHidden)

    def setTabText(self, index, text):
        tabText = text

        # Avoid Alt+letter shortcuts
        tabText.replace('&', '&&')

        tab = self.webTab(index)
        if tab and tab.isPinned():
            tabText = ''

        self.setTabToolTip(index, text)
        super(TabBar, self).setTabText(index, tabText)

    # override
    def wheelEvent(self, event):
        if gVar.app.plugins().processWheelEvent(const.ON_TabBar, self, event):
            return

        super().wheelEvent(event)

    # Q_SIGNALS
    moveAddTabButton = pyqtSignal(int)  # posX

    # private Q_SLOTS
    def _currentTabChanged(self, index):
        if not self.validIndex(index):
            return

        # Don't hide close buttons when dragging tabs
        if self._dragStartPosition.isNull():
            self._showCloseButton(index)
            if self._lastTab:
                self._hideCloseButton(self._lastTab.tabIndex())
            QTimer.singleShot(100, self.ensureVisible)

        self._lastTab = self.webTab(index)
        self._tabWidget.currentTabChanged(index)

    def _overflowChanged(self, overflowed):
        # Make sure close buttons on inactive tabs are hidden
        # This is needed for when leaving fullscreen from non-overflowed to
        # overflowed state
        import ipdb; ipdb.set_trace()
        if overflowed and self._showCloseOnInactive != 1:
            self.setTabsCloseable(False)
            self._showCloseButton(self.currentIndex())

    #def _closeTabFromButton(self):
    #    pass

    # private:
    def _validIndex(self, index):
        return index > 0 and index < self.count()

    # override
    def tabInserted(self, index):
        # Initialize pinned tab metrics
        if self.tabMetrics().pinnedWidth() == -1:

            def tabInsertedFunc():
                if self.tabMetrics().pinnedWidth() != -1:
                    return
                w = self.tabButton(0, self.iconButtonPosition())
                if w and w.parentWidget():
                    # QRect
                    wg = w.parentWidget().geometry()
                    wr = QStyle.visualRect(self.layoutDirection(), wg, w.geometry())
                    self.tabMetrics().setPinnedWidth(self.iconButtonSize().width() + wr.x() * 2)
                    self.setUpLayout()
            QTimer.singleShot(0, tabInsertedFunc)

    # override
    def tabRemoved(self, index):
        self._showCloseButton(self.currentIndex())
        self.setVisible(not (self.count() <= 1 and self._hideTabBarWithOneTab))

        # Make sure to move add tab button to correct position when where are no
        # normal tabs
        if self.normalTabsCount() == 0:
            xForAddTabButton = self.cornerWidth(Qt.TopLeftCorner) + self.PinnedTabWidth()
            if QApplication.layoutDirection() == Qt.RightToLeft:
                xForAddTabButton = self.width() - xForAddTabButton
            self.moveAddTabButton.emit(xForAddTabButton)

    def _hideCloseButton(self, index):
        if not self.validIndex(index) or self.tabsCloseable():
            return

        button = self.tabButton(index, self.closeButtonPosition())
        if not isinstance(button, CloseButton):
            return

        self.setTabButton(index, self.closeButtonPosition(), 0)
        button.deleteLater()

    def _showCloseButton(self, index):
        if not self.validIndex(index):
            return

        # WebTab
        webTab = self._tabWidget.widget(index)
        button = self.tabButton(index, self.closeButtonPosition())

        if button or (webTab and webTab.isPinned()):
            return

        self.insertCloseButton(index)

    def _updatePinnedTabCloseButton(self, index):
        if not self.validIndex(index):
            return

        webTab = self._tabWidget.widget(index)
        button = self.tabButton(index, self.closeButtonPosition())
        pinned = webTab.isPinned()

        if pinned:
            if button:
                button.hide()
        else:
            if button:
                button.show()
            else:
                self._showCloseButton(index)

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        if self.isDragInProgress():
            return

        index = self.tabAt(event.pos())

        menu = TabContextMenu(index, self._window)

        # Prevent choosing first option with double rightclick
        pos = event.globalPos()
        p = QPoint(pos.x(), pos.y() + 1)
        menu.exec_(p)

    # override
    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if gVar.app.plugins().processMouseDoubleClick(const.ON_TabBar, self, event):
            return

        if event.buttons() == Qt.LeftButton and self.emptyArea(event.pos()):
            self._tabWidget.addViewByReq(QUrl(), const.NT_SelectedTabAtTheEnd, True)
            return

        super().mouseDoubleClickEvent(event)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mousePressEvent(event)

        if gVar.app.plugins().processMousePress(const.ON_TabBar, self, event):
            return

        if event.buttons() == Qt.LeftButton and not self.emptyArea(event.pos()):
            self._dragStartPosition = event.pos()
        else:
            self._dragStartPosition = QPoint()

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mouseMoveEvent(event)

        if gVar.app.plugins().processMouseMove(const.ON_TabBar, self, event):
            return

        if self.count() == 1 and gVar.app.windowCount() == 1:
            return

        if not self._dragStartPosition.isNull():
            offset = 0
            eventY = event.pos().y()
            if eventY < 0:
                offset = abs(eventY)
            elif eventY > self.height():
                offset = eventY - self.height()
            if offset > QApplication.startDragDistance() * 3:
                global_ = self.mapToGlobal(self._dragStartPosition)
                w = QApplication.widgetAt(global_)
                if w:
                    mouse = QMouseEvent(QEvent.MouseButtonRelease, w.mapFromGlobal(global_),
                            Qt.LeftButton, Qt.LeftButton, event.modifiers())
                    QApplication.sendEvent(w, mouse)
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData(self.MIMETYPE, b'')
                drag.setMimeData(mime)
                drag.setPixmap(self.tabPixmap(self.currentIndex()))
                if drag.exec_() == Qt.IgnoreAction:
                    self._tabWidget.detachTab(self.currentIndex())
                return

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mouseReleaseEvent(event)

        self._dragStartPosition = QPoint()

        if gVar.app.plugins().processMouseRelease(const.ON_TabBar, self, event):
            return

        if not self.rect().contains(event.pos()):
            return

        if event.button() == Qt.MiddleButton:
            if self.emptyArea(event.pos()):
                self._tabWidget.addViewByReq(QUrl(), const.NT_SelectedTabAtTheEnd, True)
                return

            id_ = self.tabAt(event.pos())
            if id_ != -1:
                self._tabWidget.requestCloseTab(id_)
                return

    # override
    def dragEnterEvent(self, event):
        '''
        @param: event QDragEnterEvent
        '''
        print('dragEnterEvent')
        pass

    # override
    def dragMoveEvent(self, event):
        '''
        @param: event QDragMoveEvent
        '''
        print('dragMoveEvent')
        pass

    # override
    def dragLeaveEvent(self, event):
        '''
        @param: event QDragLeaveEvent
        '''
        print('dragLeaveEvent')
        pass

    # override
    def dropEvent(self, event):
        '''
        @param: event QDropEvent
        '''
        print('dropEvent')
        pass

    # override
    def tabSizeHint(self, index, fast):  # noqa C901
        '''
        @return: QSize
        '''
        if not self._window.isVisible():
            # Don't calculate it when window is not visible
            # It produces invalid size anyway
            return QSize(-1, -1)

        pinnedTabWidth = self._comboTabBarPixelMetric(ComboTabBar.PinnedTabWidth)
        minTabWith = self._comboTabBarPixelMetric(ComboTabBar.NormalTabMinimumWidth)

        size = super().tabSizeHint(index)

        # The overflowed tabs have same size and we can use this fast method
        if fast:
            if index >= self.pinnedTabsCount():
                size.setWidth(minTabWith)
            else:
                size.setWidth(pinnedTabWidth)
            return size

        # TODO: WebTab* webTab =
        # qobject_cast<WebTab*>(m_tabWidget->widget(index));
        webTab = self._tabWidget.widget(index)
        # TODO: TabBar* tabBar = const_cast <TabBar*>(this);
        tabBar = self

        if webTab and webTab.isPinned():
            size.setWidth(pinnedTabWidth)
        else:
            availableWidth = self._mainTabBarWidth() - self._comboTabBarPixelMetric(self.ExtraReservedWidth)
            if availableWidth < 0:
                return QSize(-1, -1)

            normalTabsCount = super().normalTabsCount()
            maxTabWidth = self._comboTabBarPixelMetric(ComboTabBar.NormalTabMaximumWidth)

            if availableWidth >= maxTabWidth * normalTabsCount:
                self._normalTabWidth = maxTabWidth
                size.setWidth(self._normalTabWidth)
            elif normalTabsCount > 0:
                minActiveTabWidth = self._comboTabBarPixelMetric(ComboTabBar.ActiveTabMinimumWidth)

                maxWidthForTab = availableWidth / normalTabsCount
                realTabWidth = maxWidthForTab
                adjustingActiveTab = False

                if realTabWidth < minActiveTabWidth:
                    if normalTabsCount > 1:
                        maxWidthForTab = (availableWidth - minActiveTabWidth) / (normalTabsCount - 1)
                    else:
                        maxWidthForTab = 0
                    realTabWidth = minActiveTabWidth
                    adjustingActiveTab = True

                tryAdjusting = availableWidth >= minTabWith * normalTabsCount

                if self._showCloseOnInactive != 1 and self.tabsCloseable() and \
                        availableWidth < (minTabWith + 25) * normalTabsCount:
                    # Hiding close buttons to save some space
                    tabBar.setTabsCloseable(False)
                    tabBar._showCloseButton(self.currentIndex())
                if self._showCloseOnInactive == 1:
                    # Always showing close buttons
                    tabBar.setTabsCloseable(True)
                    tabBar._showCloseButton(self.currentIndex())

                if tryAdjusting:
                    self._normalTabWidth = maxWidthForTab

                    # Fill any empty space (we've got from rounding) with active tab
                    if index == self.mainTabBarCurrentIndex():
                        if adjustingActiveTab:
                            self._activeTabWidth = (availableWidth - minActiveTabWidth -
                                    maxWidthForTab * (normalTabsCount - 1)) + realTabWidth
                        else:
                            self._activeTabWidth = (availableWidth -
                                    maxWidthForTab * normalTabsCount) + maxWidthForTab
                        size.setWidth(self._activeTabWidth)
                    else:
                        size.setWidth(self._normalTabWidth)

            # Restore close buttons according to preferences

            if self._showCloseOnInactive != 2 and not self.tabsCloseable() and \
                    availableWidth >= (minTabWith + 25) * normalTabsCount:
                tabBar.setTabsCloseable(True)

                # Hide close buttons on pinned tabs
                for idx in range(self.count()):
                    tabBar._updatePinnedTabCloseButton(idx)

        if index == self.count() - 1:
            # TODO: WebTab* lastMainActiveTab = qobject_cast<WebTab*>(m_tabWidget->widget(mainTabBarCurrentIndex()));
            lastMainActiveTab = self._tabWidget.widget(self.mainTabBarCurrentIndex())
            xForAddTabButton = self.cornerWidth(Qt.TopLeftCorner) + pinnedTabWidth + \
                self.normalTabsCount() + self._normalTabWidth

            if lastMainActiveTab and self._activeTabWidth > self._normalTabWidth:
                xForAddTabButton += self._activeTabWidth - self._normalTabWidth

            if QApplication.layoutDirection() == Qt.RightToLeft:
                xForAddTabButton = self.width() - xForAddTabButton

            tabBar.moveAddTabButton.emit(xForAddTabButton)

        return size

    def comboTabBarPixelMetric(self, sizeType):
        '''
        @param: sizeType ComboTabBar::SizeType
        '''
        if sizeType == self.PinnedTabWidth:
            result = self.tabMetrics().pinnedWidth()
            if result > 0: return result
            else: return 32
        elif sizeType == self.ActiveTabMinimumWidth:
            return self.tabMetrics().activeMinWidth()
        elif sizeType == self.NormalTabMinimumWidth:
            return self.tabMetrics().normalMinWidth()
        elif sizeType == self.OverflowedTabWidth:
            return self.tabMetrics().overflowedWidth()
        elif sizeType == self.NormalTabMaximumWidth:
            return self.tabMetrics().normalMaxWidth()
        elif sizeType == self.ExtraReservedWidth:
            return self._tabWidget.extraReservedWidth()

        return -1

    def webTab(self, index=-1):
        '''
        @return: WebTab
        '''
        if index == -1:
            result = self._tabWidget.widget(self.currentIndex())
        else:
            result = self._tabWidget.widget(index)
        if isinstance(result, WebTab):
            return result
        else:
            return None
