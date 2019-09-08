from mc.tools.ToolButton import ToolButton
from PyQt5.Qt import QTimer
from PyQt5.Qt import pyqtSignal

class ReloadStopButton(ToolButton):
    def __init__(self, parent=0):
        super().__init__(parent)
        self._loadInProgress = False
        self._updateTime = QTimer()

    def showStopButton(self):
        pass

    def showReloadButton(self):
        pass

    # public Q_SIGNALS
    stopClicked = pyqtSignal()
    reloadClicked = pyqtSignal()

    # private Q_SLOTS
    def _updateButton(self):
        pass

    def _buttonClicked(self):
        pass
