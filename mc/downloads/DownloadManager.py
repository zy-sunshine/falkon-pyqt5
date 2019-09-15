from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QBasicTimer
from PyQt5.Qt import QSize
from PyQt5.Qt import pyqtSignal

class DownloadManager(QWidget):

    # DownloadOption
    OpenFile = 0
    SaveFile = 1
    ExternalManager = 2
    NoOption = 3

    class DownloadInfo:
        def __init__(self, page):
            '''
            @param: page WebPage
            '''
            self.page = page  # WebPage
            self.suggestedFileName = ''

            self.askWhatToDo = True
            self.forceChoosingPath = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = None  # Ui::DownloadManager
        self._timer = QBasicTimer()

        self._lastDownloadPath = ''
        self._downloadPath = ''
        self._useNativeDialog = False
        self._isClosing = False
        self._closeOnFinish = False
        self._activeDownloadsCount = 0

        self._useExternalManager = False
        self._externalExecutable = ''
        self._externalArguments = ''

        self._lastDownloadOption = self.SaveFile  # DownloadOption

        self._taskbarButton = None  # QPointer<QWinTaskbarButton>

    def loadSettings(self):
        pass

    def download(self, downloadItem):
        '''
        @param: downloadItem QWebEngineDownloadItem
        '''
        pass

    def downloadsCount(self):
        # TODO:
        return 0

    def activeDownloadsCount(self):
        # TODO:
        return 0

    def canClose(self):
        '''
        @return: bool
        '''
        pass

    def useExternalManager(self):
        '''
        @return: bool
        '''
        pass

    def startExternalManager(self, url):
        '''
        param: url QUrl
        '''
        pass

    def setLastDownloadPath(self, lastPath):
        self._lastDownloadPath = lastPath

    def setLastDownloadOption(self, option):
        self._lastDownloadOption = option

    # public Q_SLOTS:
    def show(self):
        pass

    # private Q_SLOTS:
    def _clearList(self):
        pass

    def _deleteItem(self, item):
        '''
        @parma: item DownloadItem
        '''
        pass

    def _downloadFinished(self, success):
        '''
        @param: success bool
        '''
        pass

    # Q_SIGNALS
    resized = pyqtSignal(QSize)
    downloadsCountChanged = pyqtSignal()

    # private:
    # override
    def timerEvent(self, event):
        '''
        @param: event QTimerEvent
        '''
        pass

    # override
    def closeEvent(self, event):
        '''
        @param: event QCloseEvent
        '''
        pass

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        pass

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass

    # override
    def closeDownloadTab(self, item):
        '''
        @param: item QWebEngineDownloadItem
        '''
        pass

    def taskbarButton(self):
        '''
        @return: QWinTaskbarButton
        '''
        pass
