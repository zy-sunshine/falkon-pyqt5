from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QStyle
from PyQt5.Qt import QIcon
from PyQt5.Qt import QSizePolicy

class DockTitleBarWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('mc/tools/DockTitleBarWidget.ui', self)
        self.ui.closeButton.setIcon(QIcon(IconProvider.standardIcon(QStyle.SP_DialogCloseButton).pixmap(16)))
        self.ui.label.setText(title)
        self.ui.closeButton.clicked.connect(parent.close)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def setTitle(self, title):
        self.ui.label.setText(title)
