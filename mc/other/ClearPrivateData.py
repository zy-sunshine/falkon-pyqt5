from PyQt5.Qt import QDialog
from PyQt5.Qt import pyqtSlot

class ClearPrivateData(QDialog):
    def clearLocalStorage(self):
        pass

    def clearWebDatabases(self):
        pass

    def clearCache(self):
        pass

    # Q_SLOTS
    @pyqtSlot(bool)
    def historyClicked(state):
        pass

    @pyqtSlot()
    def dialogAccepted(self):
        pass

    @pyqtSlot()
    def optimizeDb(self):
        pass

    @pyqtSlot()
    def showCookieManager(self):
        pass
