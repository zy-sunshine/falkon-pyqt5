from mc.tools.EnhancedMenu import Menu
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QIcon
from PyQt5.Qt import QAction
from mc.common.globalvars import gVar
from .BookmarksTools import BookmarksTools
from .BookmarkItem import BookmarkItem

class BookmarksMenu(Menu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window = None  # QPointer<BrowserWindow>
        self._changed = True
        self._init()

        bookmarks = gVar.app.bookmarks()
        bookmarks.bookmarkAdded.connect(self._bookmarksChanged)
        bookmarks.bookmarkRemoved.connect(self._bookmarksChanged)
        bookmarks.bookmarkChanged.connect(self._bookmarksChanged)

    def setMainWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._window = window

    # private Q_SLOTS:
    def _bookmarkPage(self):
        if self._window:
            self._window.bookmarkPage()

    def _bookmarkAllTabs(self):
        if self._window:
            BookmarksTools.bookmarkAllTabsDialog(self._window, self._window.tabWidget())

    def _showBookmarksManager(self):
        print('-----> here', self._window)
        if self._window:
            gVar.app.browsingLibrary().showBookmarks(self._window)

    def _bookmarksChanged(self):
        self._changed = True

    def _aboutToShow(self):
        if self._changed:
            self._refresh()
            self._changed = False

    def _menuAboutToShow(self):
        menu = self.sender()
        assert(isinstance(menu, Menu))

        for action in menu.actions():
            item = action.data()
            if isinstance(item, BookmarkItem) and item.type() == BookmarkItem.Url and action.icon().isNull():
                action.setIcon(item.icon())

    def _menuMiddleClicked(self, menu):
        '''
        @param: menu Menu
        '''
        item = menu.menuAction().data()
        assert(isinstance(item, BookmarkItem))
        self._openFolder(item)

    def _bookmarkActivated(self):
        action = self.sender()
        if isinstance(action, QAction):
            item = action.data()
            assert(isinstance(item, BookmarkItem))
            self._openBookmark(item)

    def _bookmarkCtrlActivated(self):
        action = self.sender()
        if isinstance(action, QAction):
            item = action.data()
            assert(isinstance(item, BookmarkItem))
            self._openBookmarkInNewTab(item)

    def _bookmarkShiftActivated(self):
        action = self.sender()
        if isinstance(action, QAction):
            item = action.data()
            assert(isinstance(item, BookmarkItem))
            self._openBookmarkInNewWindow(item)

    def _openFolder(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item.isFolder())

        if self._window:
            BookmarksTools.openFolderInTabs(self._window, item)

    def _openBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item.isUrl())

        if self._window:
            BookmarksTools.openBookmark(self._window, item)

    def _openBookmarkInNewTab(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item.isUrl())

        if self._window:
            BookmarksTools.openBookmarkInNewTab(self._window, item)

    def _openBookmarkInNewWindow(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item.isUrl())

        if self._window:
            BookmarksTools.openBookmarkInNewWindow(self._window, item)

    # private:
    def _init(self):
        self.setTitle('&Bookmarks')

        act = self.addAction('Bookmark &This Page', self._bookmarkPage)
        act.setShortcut(QKeySequence('Ctrl+D'))
        self.addAction('Bookmark &All Tabs', self._bookmarkAllTabs)
        act = self.addAction(QIcon.fromTheme('bookmarks-organize'),
            'Organize &Bookmarks')
        # NOTE: if use self.addAction(icon, label, self._showBookmarksManager)
        # will cause connection random invalid, so here connect triggered
        # separately.
        act.triggered.connect(self._showBookmarksManager)
        act.setShortcut(QKeySequence('Ctrl+Shift+O'))
        self.addSeparator()

        self.aboutToShow.connect(self._aboutToShow)
        self.aboutToShow.connect(self._menuAboutToShow)
        self.menuMiddleClicked.connect(self._menuMiddleClicked)

    def _refresh(self):
        while len(self.actions()) > 4:
            act = self.actions()[4]
            if act.menu():
                act.menu().clear()
            self.removeAction(act)
            del act

        BookmarksTools.addActionToMenu(self, self, gVar.app.bookmarks().toolbarFolder())
        self.addSeparator()

        for child in gVar.app.bookmarks().menuFolder().children():
            BookmarksTools.addActionToMenu(self, self, child)

        self.addSeparator()
        BookmarksTools.addActionToMenu(self, self, gVar.app.bookmarks().unsortedFolder())
