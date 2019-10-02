from PyQt5.Qt import QApplication
from PyQt5.Qt import pyqtSignal

class QtSingleApp(QApplication):
    def __init__(self, *args, **kwargs):
        super(QtSingleApp, self).__init__(*args, **kwargs)
        self._appId = ''
        self._isRunning = False

    def appId(self):
        return self._appId

    def setAppId(self, appId):
        self._appId = appId

    def isRunning(self):
        return self._isRunning

    # Q_SIGNALS
    messageReceived = pyqtSignal(str)  # message

    def removeLockFile(self):
        pass
