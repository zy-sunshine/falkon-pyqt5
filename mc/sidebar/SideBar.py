from PyQt5.Qt import QObject
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import Qt
from PyQt5.Qt import QVBoxLayout
from mc.tools.DockTitleBarWidget import DockTitleBarWidget
from PyQt5.Qt import QActionGroup
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QAction
from mc.common.globalvars import gVar
from .BookmarksSideBar import BookmarksSideBar
from .HistorySideBar import HistorySideBar

class SideBar(QWidget):
    def __init__(self, manager, window):
        super().__init__(window)
        self._window = window  # BrowserWindow
        self._layout = None  # QVBoxLayout
        self._titleBar = None  # DockTitleBarWidget
        self._manager = manager  # SideBarManager

        self.setObjectName('sidebar')
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self._titleBar = DockTitleBarWidget('', self)
        self._layout.addWidget(self._titleBar)

    def showBookmarks(self):
        self._titleBar.setTitle(_('Bookmarks'))
        bar = BookmarksSideBar(self._window)
        self.setWidget(bar)

    def showHistory(self):
        self._titleBar.setTitle(_('History'))
        bar = HistorySideBar(self._window)
        self.setWidget(bar)

    def setTitle(self, title):
        self._titleBar.setTitle(title)

    def setWidget(self, widget):
        if self._layout.count() == 2:
            self._layout.removeItem(1)

        if widget:
            self._layout.addWidget(widget)

    # Q_SLOTS
    def close(self):
        self._manager.closeSideBar()

        p = self.parentWidget()
        if p:
            p.setFocus()

        super().close()

class SideBarManager(QObject):
    # for plugins only
    _s_sidebars = {}  # QHash<QString, QPointer<SideBarInterface>>
    def __init__(self, parent):
        '''
        @param: parent BrowserWindow
        '''
        super().__init__(parent)
        self._window = parent
        self._sideBar = None  # QPointer<SideBar>
        self._menu = None  # QMenu
        self._activeBar = ''

    def activeSideBar(self):
        '''
        @return: QString
        '''
        return self._activeBar

    def createMenu(self, menu):
        '''
        @param: menu QMenu
        '''
        self._window.removeActions(menu.actions())
        menu.clear()

        group = QActionGroup(menu)

        act = menu.addAction(_('Bookmarks'), self._slotShowSideBar)
        act.setCheckable(True)
        act.setShortcut(QKeySequence('Ctrl+Shift+B'))
        act.setData('Bookmarks')
        act.setChecked(self._activeBar == 'Bookmarks')
        group.addAction(act)

        act = menu.addAction(_('History'), self._slotShowSideBar)
        act.setCheckable(True)
        act.setShortcut(QKeySequence('Ctrl+H'))
        act.setData('History')
        act.setChecked(self._activeBar == 'History')
        group.addAction(act)

        for key, sidebar in self._s_sidebars.items():
            if not sidebar: continue
            # QAction
            act = sidebar.createMenuAction()
            act.setData(key)
            act.setChecked(self._activeBar == key)
            act.triggered.connect(self._slotShowSideBar)
            menu.addAction(act)
            group.addAction(act)

        self._window.addActions(menu.actions())

    def showSideBar(self, id_, toggle=True):
        '''
        @param: id_ QString
        '''
        if not id_ or id_ == 'None':
            return

        if not self._sideBar:
            self._sideBar = self._window.addSideBar()

            def destroyedFunc():
                self._activeBar = ''
                self._window.saveSideBarSettings()
            self._sideBar.destroyed.connect(destroyedFunc)

        if id_ == self._activeBar:
            if not toggle:
                return
            self._sideBar.close()
            self._activeBar = ''
            self._window.saveSideBarSettings()
            return

        if id_ == 'Bookmarks':
            self._sideBar.showBookmarks()
        elif id_ == 'History':
            self._sideBar.showHistory()
        else:
            sidebar = self._s_sidebars.get(id_)
            if not sidebar:
                self._sideBar.close()
                return

            self._sideBar.setTitle(sidebar.title())
            self._sideBar.setWidget(sidebar.createSideBarWidget(self._window))

        self._activeBar = id_
        self._window.saveSideBarSettings()

    def sideBarRemoved(self, id_):
        '''
        @param: id_ QString
        '''
        if self._activeBar == id_ and self._sideBar:
            self._sideBar.setWidget(None)
            self._sideBar.close()

    def closeSideBar(self):
        if gVar.app.isClosing():
            return

        self._activeBar = ''
        self._window.saveSideBarSettings()

    def addSidebar(self, id_, interface):
        '''
        @param: id_ QString
        @param: interface SideBarInterface
        '''
        self._s_sidebars[id_] = interface

    def removeSidebar(self, interface):
        '''
        @param: interface SideBarInterface
        '''
        id_ = ''
        for key, interf in self._s_sidebars.items():
            if interface == interf:
                id_ = key
                break
        else:
            return

        self._s_sidebars.pop(id_)

        for window in gVar.app.windows():
            window.sideBarManager().sideBarRemoved(id_)

    # Q_SLOTS
    def _slotShowSideBar(self):
        act = self.sender()
        if isinstance(act, QAction):
            self.showSideBar(act.data())
