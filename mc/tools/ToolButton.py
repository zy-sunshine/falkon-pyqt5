from PyQt5.Qt import QImage
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QTimer
from PyQt5.QtWidgets import QToolButton
from PyQt5.Qt import QIcon
from PyQt5.Qt import QStyleOption
from PyQt5.Qt import QStyle
from PyQt5.Qt import QSize
from PyQt5.Qt import QPoint
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import Qt
from PyQt5.Qt import QStyleOptionToolButton
from PyQt5.Qt import QPainter
from PyQt5.Qt import pyqtProperty

class ToolButton(QToolButton):
    _MultiIconOption = 1
    _ShowMenuInsideOption = 2
    _ToolBarLookOption = 4
    _ShowMenuOnRightClick = 8
    def __init__(self, parent=None):
        super(ToolButton, self).__init__(parent)
        self._multiIcon = QImage()
        self._themeIcon = ''
        self._pressTimer = QTimer()
        self._menu = None  # QMenu
        self._options = 0

        self.setMinimumWidth(16)
        opt = QStyleOptionToolButton()
        self.initStyleOption(opt)

        self._pressTimer.setSingleShot(True)
        self._pressTimer.setInterval(QApplication.style().styleHint(
            QStyle.SH_ToolButton_PopupDelay, opt, self
        ))
        self._pressTimer.timeout.connect(self._showMenu)

    def size(self):
        return super().size()

    def setFixedSize(self, size):
        return super().setFixedSize(size)

    fixedsize = pyqtProperty(QSize, size, setFixedSize)

    def width(self):
        return super().width()

    def setFixedWidth(self, width):
        return super().setFixedWidth(width)

    fixedwidth = pyqtProperty(int, width, setFixedWidth)

    def height(self):
        return super().height()

    def setFixedHeight(self, height):
        return super().setFixedHeight(height)

    fixedheight = pyqtProperty(int, height, setFixedHeight)

    def multiIcon(self):
        '''
        @brief: MultiIcon - Image containing pixmaps for all button states
        @return: QImage
        '''
        return self._multiIcon

    def setMultiIcon(self, image):
        '''
        @param: image QImage
        '''
        self._options |= self._MultiIconOption
        self._multiIcon = image
        self.setFixedSize(self._multiIcon.width(), self._multiIcon.height())

        self.update()

    multiIcon = pyqtProperty(QImage, multiIcon, setMultiIcon)

    def icon(self):
        '''
        @brief: Icon - Standard QToolButton with icon
        @return: QIcon
        '''
        return super().icon()

    def setIcon(self, icon):
        '''
        @param: QIcon
        '''
        if self._options & self._MultiIconOption:
            self.setFixedSize(self.sizeHint())

        self._options &= ~self._MultiIconOption
        if not isinstance(icon, QIcon):
            icon = QIcon(icon)
        super().setIcon(icon)

    icon = pyqtProperty(QIcon, icon, setIcon)

    def themeIcon(self):
        '''
        @brief: ThemeIcon - Standard QToolButton with theme icon
        @return: QString
        '''
        return self._themeIcon

    def setThemeIcon(self, icon):
        '''
        @param: icon QString
        '''
        # QIcon ic
        ic = QIcon.fromTheme(icon)
        if not ic.isNull():
            self._themeIcon = icon
            self.setIcon(QIcon.fromTheme(self._themeIcon))

    themeIcon = pyqtProperty(str, themeIcon, setThemeIcon)

    def fallbackIcon(self):
        '''
        @brief: FallbackIcon - In case theme doesn't contain ThemeIcon
        @return: QIcon
        '''
        return self.icon

    def setFallbackIcon(self, fallbackIcon):
        '''
        @param: fallbackIcon QIcon
        '''
        if self.icon.isNull():
            self.setIcon(fallbackIcon)

    fallbackIcon = pyqtProperty(QIcon, fallbackIcon, setFallbackIcon)

    def menu(self):
        '''
        @note: Menu - Menu is handled in ToolButton and is not passed to QToolButton
            There won't be menu indicator shown in the button
            QToolButton::MenuButtonPopup is not supported
        @return: QMenu
        '''
        return self._menu

    def setMenu(self, menu):
        '''
        @param: menu QMenu
        '''
        assert(menu)

        if self._menu:
            self._menu.aboutToHide.disconnect(self._menuAboutToHide)

        self._menu = menu
        self._menu.aboutToHide.connect(self._menuAboutToHide)

    def showMenuInside(self):
        '''
        @brief: Align the right corner of menu to the right corner of button
        '''
        return self._options & self._ShowMenuInsideOption

    def setShowMenuInside(self, enable):
        if enable:
            self._options |= self._ShowMenuInsideOption
        else:
            self._options &= ~self._ShowMenuInsideOption

    def showMenuOnRightClick(self):
        '''
        @brief: Show button menu on right click
        '''
        return self._options & self._ShowMenuOnRightClick

    def setShowMenuOnRightClick(self, enable):
        if enable:
            self._options |= self._ShowMenuOnRightClick
        else:
            self._options &= ~self._ShowMenuOnRightClick

    def toolbarButtonLook(self):
        '''
        @brief: Set the button to look as it was in toolbar
            (it now only sets the correct icon size)
        @return: bool
        '''
        return self._options & self._ToolBarLookOption

    def setToolbarButtonLook(self, enable):
        if enable:
            self._options |= self._ToolBarLookOption

            opt = QStyleOption()
            opt.initFrom(self)
            size = self.style().pixelMetric(QStyle.PM_ToolBarIconSize, opt, self)
            self.setIconSize(QSize(size, size))
        else:
            self._options &= ~self._ToolBarLookOption

        self.setProperty('toolbar-look', enable)
        self.style().unpolish(self)
        self.style().polish(self)

    # Q_SIGNALS
    middleMouseClicked = pyqtSignal()
    controlClicked = pyqtSignal()
    doubleClicked = pyqtSignal()

    # It is needed to use these signals with ShowMenuInside
    aboutToShowMenu = pyqtSignal()
    aboutToHideMenu = pyqtSignal()

    # private Q_SLOTS
    def _menuAboutToHide(self):
        self.setDown(False)
        self.aboutToHideMenu.emit()

    def _showMenu(self):
        if not self._menu or self._menu.isVisible():
            return

        self.aboutToShowMenu.emit()

        pos = QPoint()

        if self._options & self._ShowMenuInsideOption:
            pos = self.mapToGlobal(self.rect().bottomRight())
            if QApplication.layoutDirection() == Qt.RightToLeft:
                pos.setX(pos.x() - self.rect().width())
            else:
                pos.setX(pos.x() - self._menu.sizeHint().width())
        else:
            pos = self.mapToGlobal(self.rect().bottomLeft())

        self._menu.popup(pos)

    # protected:
    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        buttons = event.buttons()
        if buttons == Qt.LeftButton and self.popupMode() == QToolButton.DelayedPopup:
            self._pressTimer.start()

        if buttons == Qt.LeftButton and self.menu() and self.popupMode() == QToolButton.InstantPopup:
            self.setDown(True)
            self._showMenu()
        elif buttons == Qt.RightButton and self.menu() and self._options & self.showMenuOnRightClick:
            self.setDown(True)
            self._showMenu()
        else:
            super().mousePressEvent(event)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        self._pressTimer.stop()

        button = event.button()
        if button == Qt.MiddleButton and self.rect().contains(event.pos()):
            self.middleMouseClicked.emit()
            self.setDown(False)
        elif button == Qt.LeftButton and self.rect().contains(event.pos()) and \
                event.modifiers() == Qt.ControlModifier:
            self.controlClicked.emit()
            self.setDown(False)
        else:
            super().mouseReleaseEvent(event)

    # override
    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mouseDoubleClickEvent(event)

        self._pressTimer.stop()

        if event.buttons() == Qt.LeftButton:
            self.doubleClicked.emit()

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        # Block to prevent showing both context menu and button menu
        if self.menu() and self._options & self._ShowMenuOnRightClick:
            return

        super().contextMenuEvent(event)

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        if not (self._options & self._MultiIconOption):
            super().paintEvent(event)
            return

        p = QPainter(self)

        w = self._multiIcon.width()
        h4 = self._multiIcon.height() / 4

        if not self.isEnabled():
            p.drawImage(0, 0, self._multiIcon, 0, h4 * 3, w, h4)
        elif self.isDown():
            p.drawImage(0, 0, self._multiIcon, 0, h4 * 2, w, h4)
        elif self.underMouse():
            p.drawImage(0, 0, self._multiIcon, 0, h4 * 1, w, h4)
        else:
            p.drawImage(0, 0, self._multiIcon, 0, h4 * 0, w, h4)
