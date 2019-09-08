from PyQt5.QtWidgets import QLabel
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIcon
from PyQt5.Qt import QPoint

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._themeIcon = ''
        self._fallbackIcon = QIcon()

    def themeIcon(self):
        '''
        @return: QString
        '''
        pass

    def setThemeIcon(self, name):
        pass

    def fallbackIcon(self):
        '''
        @return: QIcon
        '''
        pass

    def setFallbackIcon(self, fallbackIcon):
        '''
        @param: fallbackIcon QIcon
        '''
        pass

    # public Q_SIGNALS
    clicked = pyqtSignal(QPoint)
    middleClicked = pyqtSignal(QPoint)

    # private:
    def _updateIcon(self):
        pass

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        pass

    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass
