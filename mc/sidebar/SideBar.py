from PyQt5.Qt import QObject

class SideBar(object):
    def __init__(self, manager, window):
        self._window = window  # BrowserWindow
        self._layout = None  # QVBoxLayout
        self._titleBar = None  # DockTitleBarWidget
        self._manager = manager  # SideBarManager

    def showBookmarks(self):
        pass

    def showHistory(self):
        pass

    def setTitle(self, title):
        pass

    def setWidget(self, widget):
        pass

    # Q_SLOTS
    def close(self):
        pass


class SideBarManager(QObject):
    def __init__(self, parent):
        '''
        @param: parent BrowserWindow
        '''
        super(SideBarManager, self).__init__(parent)
        self._window = parent
        self._sideBar = None  # QPointer<SideBar>
        self._menu = None  # QMenu
        self._activeBar = ''

    def activeSideBar(self):
        '''
        @return: QString
        '''
        pass

    def createMenu(self, menu):
        '''
        @param: menu QMenu
        '''
        pass

    def showSideBar(self, id, toggle=True):
        '''
        @param: id QString
        '''
        pass

    def sideBarRemoved(self, id):
        '''
        @param: id QString
        '''
        pass

    def closeSideBar(self):
        pass

    def addSidebar(self, id, interface):
        '''
        @param: id QString
        @param: interface SideBarInterface
        '''
        pass

    def removeSidebar(self, interface):
        '''
        @param: interface SideBarInterface
        '''
        pass

    # Q_SLOTS
    def _slotShowSideBar(self):
        pass
