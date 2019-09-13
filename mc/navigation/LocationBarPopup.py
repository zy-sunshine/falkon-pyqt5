from PyQt5.QtWidgets import QFrame
from PyQt5.Qt import Qt
from PyQt5.Qt import QPoint

class LocationBarPopup(QFrame):
    def __init__(self, parent):
        '''
        @param: parent QWidget
        '''
        super().__init__(parent, Qt.Popup)
        self._alignment = Qt.AlignRight

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        self.setMidLineWidth(2)

    def showAt(self, parent):
        '''
        @param: parent QWidget
        '''
        if not parent or not parent.parentWidget():
            return

        parent = parent.parentWidget()

        # Calculate sizes before showing
        self.layout().invalidate()
        self.layout().activate()

        p = parent.mapToGlobal(QPoint(0, 0))

        if self._alignment == Qt.AlignRight:
            p.setX(p.x() + parent.width() - self.width())

        p.setY(p.y() + parent.height())
        self.move(p)

        super().show()

    def setPopupAlignment(self, alignment):
        '''
        @param: alignment Qt.Alignment
        '''
        self._alignment = alignment

    def popupAlignment(self):
        '''
        @return: Qt.Alignment
        '''
        return self._alignment
