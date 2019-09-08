from PyQt5.QtWidgets import QWidget

class PopupWindow(QWidget):
    def __init__(self, view):
        super().__init__()
        self._view = view
        self._locationBar = None  # PopupLocationBar
        self._statusBarMessage = None  # PopupStatusBarMessage
        self._progressBar = None  # ProgressBar

        self._layout = None  # QVBoxLayout
        self._statusBar = None  # QStatusBar
        self._menuBar = None  # QMenuBar
        self._menuEdit = None  # QMenu
        self._menuView = None  # QMenu
        self._actionReload = None  # QAction
        self._actionStop = None  # QAction
        self._search = None  # QPointer<SearchToolBar>
        self._notificationWidget = None  # QWidget

    def statusBar(self):
        '''
        @return: QStatusBar
        '''
        pass

    def webView(self):
        '''
        @return: PopupWebView
        '''
        pass

    # public Q_SLOTS:
    def setWindowGeometry(self, newRect):
        pass

    # private Q_SLOTS:
    def _titleChanged(self):
        pass

    def _showNotification(self, notif):
        '''
        @param: notif QWidget
        '''
        pass

    def _showStatusBarMessage(self, message):
        '''
        @param: message QString
        '''
        pass

    def _loadStarted(self):
        pass

    def _loadProgress(self, value):
        pass

    def _loadFinished(self):
        pass

    def _searchOnPage(self):
        pass

    # private:
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
