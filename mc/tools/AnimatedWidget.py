from PyQt5.Qt import QTimeLine
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QPoint

class AnimatedWidget(QWidget):
    # enum Direction
    Down = 0
    Up = 1

    def __init__(self, direction=Down, duration=300, parent=None):
        '''
        @param direction Direction
        @param duration int
        @param parent QWidget
        '''
        super().__init__(parent)
        self._direction = direction
        self._timeLine = QTimeLine()
        # qreal
        self._stepHeight = 0
        # qreal
        self._stepY = 0
        self._startY = 0

        self._widget = QWidget(self)  # QWidget

        self._timeLine.setDuration(duration)
        self._timeLine.setFrameRange(0, 100)
        self._timeLine.frameChanged.connect(self._animateFrame)

        self.setMaximumHeight(0)

    def widget(self):
        return self._widget

    # public Q_SLOTS:
    def hide(self):
        if self._timeLine.state() == QTimeLine.Running:
            return

        self._timeLine.setDirection(QTimeLine.Backward)
        self._timeLine.start()

        self._timeLine.finished.connect(self.close)

        p = self.parentWidget()
        if p:
            p.setFocus()

    def startAnimation(self):
        if self._timeLine.state() == QTimeLine.Running:
            return

        shown = 0
        hidden = 0

        if self._direction == self.Down:
            shown = 0
            hidden = -1 * self._widget.height()

        self._widget.move(QPoint(self._widget.pos().x(), hidden))

        self._stepY = (hidden - shown) / 100.0
        self._startY = hidden
        self._stepHeight = self._widget.height() / 100.0

        self._timeLine.setDirection(QTimeLine.Forward)
        self._timeLine.start()

    # private Q_SLOTS:
    def _animateFrame(self, frame):
        self.setFixedHeight(frame * self._stepHeight)
        self._widget.move(self.pos().x(), self._startY - frame * self._stepY)

    # private:
    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        if event.size().width() != self._widget.width():
            self._widget.resize(event.size().width(), self._widget.height())

        super().resizeEvent(event)
