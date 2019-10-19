from PyQt5.Qt import QObject
from PyQt5.Qt import QIcon
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QAction
from PyQt5.Qt import QIODevice
from mc.common.globalvars import gVar
from mc.app.BrowserWindow import BrowserWindow
from mc.common import const

class ClosedWindowsManager(QObject):
    _s_closedWindowsVersion = 1

    class Window:
        def __init__(self):
            from mc.app.BrowserWindow import BrowserWindow
            self.icon = QIcon()
            self.title = ''
            self.windowState = BrowserWindow.SavedWindow()

        def isValid(self):
            return self.windowState.isValid()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._closedWindows = []  # QVector<Window>

    def isClosedWindowAvailable(self):
        return bool(self._closedWindows)

    def closedWindows(self):
        '''
        @return: QVector<Window>
        '''
        return self._closedWindows

    def saveWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        if gVar.app.isPrivate() or gVar.app.windowCount() == 1 or not window.weView():
            return

        closedWindow = self.Window()
        # TabbedWebView
        webView = window.weView()
        closedWindow.icon = webView.icon()
        closedWindow.title = webView.title()
        closedWindow.windowState = BrowserWindow.SavedWindow(window)
        self._closedWindows.insert(0, closedWindow)

    def takeLastClosedWindow(self):
        '''
        @brief: Takes window that was most recently closed
        '''
        if not self._closedWindows:
            return self.Window()
        return self._closedWindows.pop(0)

    def takeClosedWindowAt(self, index):
        '''
        @brief: Tasks window at given index
        @return: Window
        '''
        if index < len(self._closedWindows):
            return self._closedWindows.pop(index)
        else:
            return self.Window()

    def saveState(self):
        '''
        @return: QByteArray
        '''
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)

        stream.writeInt(self._s_closedWindowsVersion)

        # Only save last 3 windows
        windowCount = min(max(0, len(self._closedWindows)), 3)
        stream.writeInt(windowCount)

        for window in self._closedWindows[:windowCount]:
            stream.writeQVariant(window.windowState)

        return data

    def restoreState(self, state):
        '''
        @param: state QByteArray
        '''
        stream = QDataStream(state)

        version = stream.readInt()

        if version < 1:
            return

        self._closedWindows.clear()

        windowCount = stream.readInt()

        for idx in range(windowCount):
            window = self.Window()
            window.windowState = stream.readQVariant()
            if not window.isValid():
                continue
            window.icon = window.windowState.tabs[0].icon
            window.title = window.windowState.tabs[0].title
            self._closedWindows.append(window)

    # public Q_SLOTS:
    def restoreClosedWindow(self):
        act = self.sender()
        if isinstance(act, QAction):
            window = self.takeClosedWindowAt(int(act.data()))
        else:
            window = self.takeLastClosedWindow()

        if not window.isValid():
            return

        gVar.app.createWindow(const.BW_OtherRestoredWindow).restoreWindow(window.windowState)

    def restoreAllClosedWindows(self):
        for idx in range(len(self._closedWindows)):
            self.restoreClosedWindow()

    def clearClosedWindows(self):
        self._closedWindows.clear()
