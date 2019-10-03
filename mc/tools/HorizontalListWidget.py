from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListView
from PyQt5.Qt import Qt

class HorizontalListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouseDown = False
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMovement(QListView.Static)
        self.setResizeMode(QListView.Adjust)
        self.setViewMode(QListView.IconMode)
        self.setSelectionRectVisible(False)

    # private:
    # override
    def mousePressEvent(self, event):
        '''
        @param: QMouseEvent
        '''
        self._mouseDown = True

        super().mousePressEvent(event)

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if not self.itemAt(event.pos()):
            # Don't unselect item so it ends up with no item selected
            # TODO: ?
            return

        super().mouseMoveEvent(event)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        self._mouseDown = False

        super().mouseReleaseEvent(event)

    # override
    def wheelEvent(self, event):
        '''
        @param: event QWheelEvent
        '''
        # As this is just Horizontal ListWidget, disable wheel scrolling
        # completely
        pass
