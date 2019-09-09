from PyQt5.QtWidgets import QLabel
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIcon
from PyQt5.Qt import QPoint
from PyQt5.Qt import pyqtProperty
from PyQt5.Qt import QSize
from PyQt5.Qt import Qt

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._themeIcon = ''
        self._fallbackIcon = QIcon()

    def size(self):
        return super().size()

    def setFixedSize(self, sz):
        super().setFixedSize(sz)

    fixedsize = pyqtProperty(QSize, size, setFixedSize)

    def width(self):
        return super().width()

    def setFixedWidth(self, width):
        super().setFixedWidth(width)

    fixedwidth = pyqtProperty(int, width, setFixedWidth)

    def height(self):
        return super().height()

    def setFixedHeight(self, height):
        super().setFixedHeight(height)

    fixedheight = pyqtProperty(int, height, setFixedHeight)

    def themeIcon(self):
        '''
        @return: QString
        '''
        return self._themeIcon

    def setThemeIcon(self, name):
        '''
        @param: name QString
        '''
        self._themeIcon = name
        self._updateIcon()

    themeIcon = pyqtProperty(str, themeIcon, setThemeIcon)

    def fallbackIcon(self):
        '''
        @return: QIcon
        '''
        return self._fallbackIcon

    def setFallbackIcon(self, fallbackIcon):
        '''
        @param: fallbackIcon QIcon
        '''
        self._fallbackIcon = fallbackIcon
        self._updateIcon()

    fallbackIcon = pyqtProperty(QIcon, fallbackIcon, setFallbackIcon)

    # public Q_SIGNALS
    clicked = pyqtSignal(QPoint)
    middleClicked = pyqtSignal(QPoint)

    # private:
    def _updateIcon(self):
        if self._themeIcon:
            icon = QIcon.fromTheme(self._themeIcon)
            if not icon.isNull():
                self.setPixmap(icon.pixmap(self.size()))
                return

        if self._fallbackIcon:
            self.setPixmap(self._fallbackIcon.pixmap(self.size()))

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super().resizeEvent(event)
        self._updateIcon()

    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        evtBtn = event.button()
        if evtBtn == Qt.LeftButton and self.rect().contains(event.pos()):
            if event.modifiers() == Qt.ControlModifier:
                self.middleClicked.emit(event.globalPos())
            else:
                self.clicked.emit(event.globalPos())
        elif evtBtn == Qt.MiddleButton and self.rect().contains(event.pos()):
            self.middleClicked.emit(event.globalPos())
        else:
            super().mouseReleaseEvent(event)
