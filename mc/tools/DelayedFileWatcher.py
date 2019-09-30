from queue import Queue
from PyQt5.Qt import QFileSystemWatcher
from PyQt5.Qt import QTimer
from PyQt5.Qt import pyqtSignal

class DelayedFileWatcher(QFileSystemWatcher):
    def __init__(self, *args, **kwargs):
        '''
        @param: parent QObject
        @param: paths QStringList, parent QObject
        '''
        super().__init__(*args, **kwargs)
        self._dirQueue = Queue()  # QQueue<QString>
        self._fileQueue = Queue()  # Queue<QString>
        self._init()

    # private:
    def _init(self):
        super().directoryChanged.connect(self._slotDirectoryChanged)
        super().fileChanged.connect(self._slotFileChanged)

    # Q_SIGNALS
    delayedDirectoryChanged = pyqtSignal(str)  # path
    delayedFileChanged = pyqtSignal(str)  # path

    # private Q_SLOTS
    def _slotDirectoryChanged(self, path):
        '''
        @param: path QString
        '''
        self._dirQueue.put(path)
        QTimer.singleShot(500, self._dequeueDirectory)

    def _slotFileChanged(self, path):
        '''
        @param: path QString
        '''
        self._fileQueue.put(path)
        QTimer.singleShot(500, self._dequeueFile)

    def _dequeueDirectory(self):
        self.delayedDirectoryChanged.emit(self._dirQueue.get())

    def _dequeueFile(self):
        self.delayedFileChanged.emit(self._fileQueue.get())
