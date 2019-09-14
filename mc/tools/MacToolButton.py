from mc.common import const
from PyQt5.Qt import QSize
from PyQt5.Qt import pyqtProperty

# TODO: do not known why use a mac tool button here
if const.OS_MACOS:
    from PyQt5.QtWidgets import QPushButton
    class MacToolButton(QPushButton):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._autoRaise = False
            self._buttonFixedSize = QSize(18, 18)

        def setIconSize(self, size):
            super().setIconSize(size)
            self._buttonFixedSize = QSize(size.width() + 2, size.height() + 2)

        def setAutoRaise(self, enable):
            self._autoRaise = enable
            self.setFlat(enable)
            if enable:
                self.setFixedSize(self._buttonFixedSize)

        def _autoRaise(self):
            return self._autoRaise

        autoRaise = pyqtProperty(bool, _autoRaise, setAutoRaise)
else:
    from PyQt5.QtWidgets import QToolButton
    class MacToolButton(QToolButton):
        def __init__(self, parent=None):
            super().__init__(parent)
