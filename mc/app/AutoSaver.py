from PyQt5.Qt import QObject
from PyQt5.Qt import QBasicTimer
from PyQt5.Qt import pyqtSignal

class AutoSaver(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QBasicTimer()

    def saveIfNecessary(self):
        '''
        @brief: Emit save() if timer is running. Call this from destructor.
        '''
        pass

    # public Q_SLOTS:
    def changeOccurred(self):
        '''
        @brief: Tells AutoSaver that change occurred. Signal save() will be emitted after a delay
        '''
        pass

    # Q_SIGNALS:
    save = pyqtSignal()

    # private:
    # override
    def timerEvent(self, event):
        '''
        @param: event QTimerEvent
        '''
        pass
