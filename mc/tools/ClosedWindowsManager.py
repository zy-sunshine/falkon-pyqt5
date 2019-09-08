from PyQt5.Qt import QObject
from PyQt5.Qt import QIcon

class ClosedWindowsManager(QObject):

    class Window:
        def __init__(self):
            from mc.app.BrowserWindow import BrowserWindow
            self.icon = QIcon()
            self.title = ''
            self.windowState = BrowserWindow.SavedWindow()

        def isValid(self):
            return self.windowState.isValid()

    def ClosedWindowsManager(self, parent=None):
        super(ClosedWindowsManager, self).__init__(parent)
        self._closedWindows = []  # QVector<Window>

    def isClosedWindowAvailable(self):
        pass

    def closedWindows(self):
        '''
        @return: QVector<Window>
        '''
        pass

    def savedWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        pass

    def takeLastClosedWindow(self):
        '''
        @brief: Takes window that was most recently closed
        '''
        pass

    def takeClosedWindowAt(self, index):
        '''
        @brief: Tasks window at given index
        @return: Window
        '''
        pass

    def saveState(self):
        '''
        @return: QByteArray
        '''
        pass

    def restoreState(self, state):
        '''
        @param: state QByteArray
        '''
        pass

    # public Q_SLOTS:
    def restoreClosedWindow(self):
        pass

    def restoreAllClosedWindows(self):
        pass

    def clearClosedWindows(self):
        pass
