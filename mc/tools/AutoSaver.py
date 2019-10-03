from PyQt5.Qt import QObject
from PyQt5.Qt import QBasicTimer
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QCoreApplication

class AutoSaver(QObject):
    SAVE_DELAY = 1000 * 10  # 10 seconds
    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QBasicTimer()
        QCoreApplication.instance().aboutToQuit.connect(self.saveIfNecessary)

    def saveIfNecessary(self):
        '''
        @brief: Emit save() if timer is running. Call this from destructor.
        '''
        if self._timer.isActive():
            self._timer.stop()
            self.save.emit()

    # public Q_SLOTS:
    def changeOccurred(self):
        '''
        @brief: Tells AutoSaver that change occurred. Signal save() will be emitted after a delay
        '''
        if not self._timer.isActive():
            self._timer.start(self.SAVE_DELAY, self)

    # Q_SIGNALS:
    save = pyqtSignal()

    # private:
    # override
    def timerEvent(self, event):
        '''
        @param: event QTimerEvent
        '''
        if event.timerId() == self._timer.timerId():
            self._timer.stop()
            self.save.emit()

        super().timerEvent(event)
