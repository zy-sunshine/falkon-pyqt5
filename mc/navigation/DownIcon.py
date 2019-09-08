from mc.tools.ClickableLabel import ClickableLabel
from PyQt5.Qt import Qt

class DownIcon(ClickableLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('locationbar-down-icon')
        self.setCursor(Qt.ArrowCursor)

    # private:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        # Prevent propagating to LocationBar
        event.accept()

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mousePressEvent(event)

        # Prevent propagating to LocationBar
        event.accept()
