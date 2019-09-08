from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QSizePolicy
from mc.common.globalvars import gVar
from PyQt5.Qt import QPainter
from PyQt5.Qt import QRect

class NavigationContainer(QWidget):
    def __init__(self, parent=None):
        super(NavigationContainer, self).__init__(parent)
        self._layout = None  # QVBoxLayout
        self._tabBar = None  # TabBar
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def addWidget(self, widget):
        '''
        @param: widget QWidget
        '''
        self._layout.addWidget(widget)

    def setTabBar(self, tabBar):
        '''
        @param: tabBar TabBar
        '''
        self._tabBar = tabBar
        self._layout.addWidget(self._tabBar)

        self.toggleTabsOnTop(gVar.qzSettings.tabsOnTop)

    def toggleTabsOnTop(self, enable):
        self.setUpdatesEnabled(False)

        self._layout.removeWidget(self._tabBar)
        index = 0
        if not enable:
            index = self._layout.count()
        self._layout.insertWidget(index, self._tabBar)
        top = enable and 2 or 0
        bottom = enable and 2 or 0
        self._layout.setContentsMargins(0, top, 0, bottom)

        self.setUpdatesEnabled(True)

    # private:
    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        super(NavigationContainer, self).paintEvent(event)
        # Draw line at the bottom of navigation bar if tabs are on top
        # To visually distinguish navigation bar from the page
        if gVar.qzSettings.tabsOnTop:
            p = QPainter(self)
            lineRect = QRect(0, self.height()-1, self.width(), 1)
            color = self.palette().window().color().darker(125)
            p.fillRect(lineRect, color)
