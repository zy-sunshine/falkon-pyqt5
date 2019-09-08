from mc.tools.ClickableLabel import ClickableLabel
from PyQt5.Qt import Qt

class GoIcon(ClickableLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('locationbar-goicon')
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusProxy(parent)

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
