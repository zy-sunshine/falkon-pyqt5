from mc.tools.EnhancedMenu import Menu
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QIcon
from mc.common.globalvars import gVar
from .BookmarksTools import BookmarksTools

class BookmarksMenu(Menu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window = None  # QPointer<BrowserWindow>
        self._changed = False
        self._init()

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
        if self._window:
            gVar.app.browsingLibrary().showBookmarks(self._window)

    def _bookmarksChanged(self):
        pass

    def _aboutToShow(self):
        pass

    def _menuAboutToShow(self):
        pass

    def _menuMiddleClicked(self, menu):
        '''
        @param: menu Menu
        '''
        # TODO: BookmarkItem* item =
        # static_cast<BookmarkItem*>(menu->menuAction()->data().value<void*>());
        item = menu.menuAction().data().value()
        assert(item)
        self._openFolder(item)

    def _bookmarkActivated(self):
        pass

    def _bookmarkCtrlActivated(self):
        pass

    def _bookmarkShiftActivated(self):
        pass

    def _openFolder(self, item):
        '''
        @param: item BookmarkItem
        '''
        pass

    def _openBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        pass

    def _openBookmarkInNewTab(self, item):
        '''
        @param: item BookmarkItem
        '''
        pass

    def _openBookmarkInNewWindow(self, item):
        '''
        @param: item BookmarkItem
        '''
        pass

    # private:
    def _init(self):
        self.setTitle('&Bookmarks')

        act = self.addAction('Bookmark &This Page', self._bookmarkPage)
        act.setShortcut(QKeySequence('Ctrl+D'))
        self.addAction('Bookmark &All Tabs', self._bookmarkAllTabs)
        act = self.addAction(QIcon.fromTheme('bookmarks-organize'),
            'Organize &Bookmarks', self._showBookmarksManager)
        act.setShortcut(QKeySequence('Ctrl+Shift+O'))
        self.addSeparator()

        self.aboutToShow.connect(self._aboutToShow)
        self.aboutToShow.connect(self._menuAboutToShow)
        self.menuMiddleClicked.connect(self._menuMiddleClicked)

    def _refresh(self):
        while len(self.actions()) != 4:
            act = self.actions()[4]
            if act.menu():
                act.menu().clear()
            self.removeAction(act)
            del act
