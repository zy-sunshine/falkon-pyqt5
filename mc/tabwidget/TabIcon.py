from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import pyqtSignal

class TabIcon(QWidget):
    def setWebTab(self, tab):
        '''
        @param: tab WebTab
        '''

    def updateIcon(self):
        pass

    # Q_SIGNALS
    resized = pyqtSignal()
