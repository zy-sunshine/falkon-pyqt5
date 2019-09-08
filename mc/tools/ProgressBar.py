from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import Qt
from PyQt5.Qt import QStylePainter
from PyQt5.Qt import QStyleOptionProgressBar
from PyQt5.Qt import QStyle

class ProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._lastPaintedValue = -1

        self.setMinimumSize(130, 16)
        self.setMaximumSize(150, 16)

    # public Q_SLOTS:
    def setValue(self, value):
        self._value = value
        if self._lastPaintedValue != self._value:
            self.update()

    # protected:
    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        paint = QStylePainter(self)

        opt = QStyleOptionProgressBar()
        self._initStyleOption(opt)

        paint.drawControl(QStyle.CE_ProgressBar, opt)

        self._lastPaintedValue = self._value

    def _initStyleOption(self, option):
        '''
        @param: option QStyleOptionProgressBar
        '''
        if not option:
            return

        option.initFrom(self)
        option.minimum = 0
        option.maximum = 100
        option.progress = self._value
        option.textAlignment = Qt.AlignLeft
        option.textVisible = False
