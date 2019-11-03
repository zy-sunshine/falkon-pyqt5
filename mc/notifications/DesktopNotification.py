from PyQt5 import uic
from PyQt5.Qt import QPoint
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QTimer
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import pyqtSignal

class DesktopNotification(QWidget):
    def __init__(self, setPosition=False):
        super().__init__(None)
        self._ui = uic.loadUi('mc/notifications/DesktopNotification.ui', self)

        self._settingPosition = setPosition
        self._dragPosition = QPoint()

        self._icon = QPixmap()
        self._heading = ''
        self._text = ''
        self._timeout = 6000
        self._timer = QTimer(self)

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                Qt.X11BypassWindowManagerHint)

        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)

        if self._settingPosition:
            self.setCursor(Qt.OpenHandCursor)

        self._savedPos = None

    closedSignal = pyqtSignal()

    def setPixmap(self, icon):
        '''
        @param: icon QPixmap
        '''
        self._icon = icon

    def setHeading(self, heading):
        '''
        @param: heading QString
        '''
        self._heading = heading

    def setText(self, text):
        '''
        @param: text QString
        '''
        self._text = text

    def setTimeout(self, timeout):
        '''
        @param: timeout int
        '''
        self._timeout = timeout

    def show(self):
        self._ui.icon.setPixmap(self._icon)
        self._ui.icon.setVisible(not self._icon.isNull())
        self._ui.heading.setText(self._heading)
        self._ui.text.setText(self._text)

        if self._settingPosition:
            self._timer.setInterval(self._timeout)
            self._timer.start()

        super().show()

    # private:
    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if not self._settingPosition:
            self.close()
            return

        if event.buttons() == Qt.LeftButton:
            self._dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        '''
        @param event QMouseEvent
        '''
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._dragPosition)
            event.accept()

    def closeEvent(self, event):
        self.closedSignal.emit()
        self._savedPos = self.pos()
        super().closeEvent(event)

    def savedPos(self):
        if not self._savedPos:
            self._savedPos = self.pos()
        return self._savedPos
