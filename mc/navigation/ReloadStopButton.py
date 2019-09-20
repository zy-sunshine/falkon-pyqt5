from mc.tools.ToolButton import ToolButton
from PyQt5.Qt import QTimer
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import Qt

class ReloadStopButton(ToolButton):
    def __init__(self, parent=0):
        super().__init__(parent)
        self._loadInProgress = False
        self._updateTimer = None

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setToolbarButtonLook(True)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.NoFocus)

        self._updateTimer = QTimer(self)
        self._updateTimer.setInterval(50)
        self._updateTimer.setSingleShot(True)
        self._updateTimer.timeout.connect(self._updateButton)

        self.clicked.connect(self._buttonClicked)

        self._updateButton()

    def showStopButton(self):
        self._loadInProgress = True
        self._updateTimer.start()

    def showReloadButton(self):
        self._loadInProgress = False
        self._updateTimer.start()

    # public Q_SIGNALS
    stopClicked = pyqtSignal()
    reloadClicked = pyqtSignal()

    # private Q_SLOTS
    def _updateButton(self):
        if self._loadInProgress:
            self.setToolTip(_('Stop'))
            self.setObjectName('navigation-button-stop')
        else:
            self.setToolTip(_('Reload'))
            self.setObjectName('navigation-button-reload')

        # Update the stylesheet for the changed object name
        self.style().unpolish(self)
        self.style().polish(self)

    def _buttonClicked(self):
        if self._loadInProgress:
            self.stopClicked.emit()
        else:
            self.reloadClicked.emit()
