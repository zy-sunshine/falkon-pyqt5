from mc.tools.ToolButton import ToolButton
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QLabel
from mc.tools.AbstractButtonInterface import AbstractButtonInterface
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QIcon
from PyQt5.Qt import QPixmap

class NavigationBarToolButton(ToolButton):
    def __init__(self, button, parent=None):
        '''
        @param: button AbstractButtonInterface
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._button = button  # AbstractButtonInterface
        self._badgeLabel = None  # QLabel

        self.setAutoRaise(True)
        self.setToolbarButtonLook(True)
        self.setFocusPolicy(Qt.NoFocus)

        self._badgeLabel = QLabel(self)
        self._badgeLabel.setObjectName('navigation-toolbutton-badge')
        font = self._badgeLabel.font()
        font.setPixelSize(self._badgeLabel.height() / 2.5)
        self._badgeLabel.setFont(font)
        self._badgeLabel.hide()

        self.setToolTip(button.toolTip())
        self._updateIcon()
        self._updateBadge()

        button.iconChanged.connect(self._updateIcon)
        button.activeChanged.connect(self._updateIcon)
        button.toolTipChanged.connect(self.setToolTip)
        button.badgeTextChanged.connect(self._updateBadge)
        button.visibleChanged.connect(self.visibilityChangedRequested)

    def updateVisibility(self):
        self.setVisible(self._button.isVisible())

    # public Q_SIGNALS:
    visibilityChangedRequested = pyqtSignal()

    # private:
    def _clicked(self):
        c = AbstractButtonInterface.ClickController()
        c.visualParent = self

        def popupPositionFunc(size):
            pos = self.mapToGlobal(self.rect().bottomRight())
            if QApplication.isRightToLeft():
                pos.setX(pos.x() - self.rect().width())
            else:
                pos.setX(pos.x() - size.width())
            c.popupOpened = True
            return pos
        c.popupPosition = popupPositionFunc

        def popupClosedFunc():
            self.setDown(False)
            # TODO: delete c
            c.__del__()
        c.popupClosed = popupClosedFunc
        self._button.clicked.emit(c)
        if c.popupOpened:
            self.setDown(True)
        else:
            c.popupClosed()

    def _updateIcon(self):
        if self._button.isActive():
            mode = QIcon.Normal
        else:
            mode = QIcon.Disabled
        img = self._button.icon().pixmap(self.iconSize(), mode).toImage()
        self.setIcon(QPixmap.fromImage(img, Qt.MonoOnly))

    def _updateBadge(self):
        if not self._button.badgeText():
            self._badgeLabel.hide()
        else:
            self._badgeLabel.setText(self._button.badgeText())
            self._badgeLabel.resize(self._badgeLabel.sizeHint())
            self._badgeLabel.move(self.width() - self._badgeLabel.width(), 0)
            self._badgeLabel.show()

    # override
    def mouseReleaseEvent(self, event):
        '''
        @brief: Prevent flickering due to mouse release event restoring Down State
        @param: event QMouseEvent
        '''
        popupOpened = False

        if event.button == Qt.LeftButton and self.rect().contains(event.pos()):
            self.clicked()
            popupOpened = self.isDown()

        if popupOpened:
            self.setUpdatesEnabled(False)

        super().mouseReleaseEvent(event)

        if popupOpened:
            self.setDown(True)
            self.setUpdatesEnabled(True)
