from PyQt5.QtWidgets import QLineEdit
from PyQt5.Qt import Qt

class FocusSelectLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouseFocusReason = False

    # public Q_SLOTS:
    def setFocus(self):
        self.selectAll()

        super().setFocus()

    # protected:
    def focusInEvent(self, event):
        '''
        @param: QFocusEvent
        '''
        self._mouseFocusReason = event.reason() == Qt.MouseFocusReason
        self.selectAll()

        super().focusInEvent(event)

    def mousePressEvent(self, event):
        '''
        @param: QMouseEvent
        '''
        if self._mouseFocusReason:
            self._mouseFocusReason = False
            return

        super().mousePressEvent(event)
