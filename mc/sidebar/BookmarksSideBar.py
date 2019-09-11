from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from mc.common.globalvars import gVar
from mc.bookmarks.BookmarksTreeView import BookmarksTreeView
from mc.bookmarks.BookmarksTools import BookmarksTools
from PyQt5.QtWidgets import QMenu
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QIcon

class BookmarksSideBar(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('BookmarksSideBar.ui')
        self._window = window
        self._bookmarks = gVar.app.bookmarks()  # Bookmarks

        self.ui.setupUi(self)
        self.ui.tree.setViewType(BookmarksTreeView.BookmarksSidebarViewType)

        self.ui.tree.bookmarkActivated.connect(self._bookmarkActived)
        self.ui.tree.bookmarkCtrlActivated.connect(self._bookmarkCtrlActived)
        self.ui.tree.bookmarkShiftActivated.connect(self._bookmarkShiftActived)
        self.ui.tree.contextMenuRequested.connect(self._createContextMenu)

        self.ui.search.textChanged.connect(self.ui.tree.search)

    # private Q_SLOTS:
    def _bookmarkActived(self, item):
        self._openBookmark(item)

    def _bookmarkCtrlActived(self, item):
        self._openBookmarkInNewTab(item)

    def _bookmarkShiftActived(self, item):
        self._openBookmarkInNewWindow(item)

    def _openBookmark(self, item=None):
        if not item:
            item = self.ui.tree.selectedBookmark()
        BookmarksTools.openBookmark(self._window, item)

    def _openBookmarkInNewTab(self, item=None):
        if not item:
            item = self.ui.tree.selectedBookmark()
        BookmarksTools.openBookmarkInNewTab(self._window, item)

    def _openBookmarkInNewWindow(self, item=None):
        if not item:
            item = self.ui.tree.selectedBookmark()
        BookmarksTools.openBookmarkInNewWindow(self._window, item)

    def _openBookmarkInNewPrivateWindow(self, item=None):
        if not item:
            item = self.ui.tree.selectedBookmark()
        BookmarksTools.openBookmarkInNewPrivateWindow(self._window, item)

    def _deleteBookmarks(self):
        items = self.ui.tree.selectedBookmarks()

        for item in items:
            if self._bookmarks.canBeModified(item):
                self._bookmarks.removeBookmark(item)

    def _createContextMenu(self, pos):
        '''
        @param: pos QPoint
        '''
        menu = QMenu()
        actNewTab = menu.addAction(IconProvider.newTabIcon(), _('Open in new tab'))
        actNewWindow = menu.addAction(IconProvider.newWindowIcon(), _('Open in new window'))
        actNewPrivateWindow = menu.addAction(IconProvider.privateBrowsingIcon(), _('Open in new private window'))

        menu.addSeparator()
        actDelete = menu.addAction(QIcon.fromTheme('edit-delete'), _('Delete'))

        actNewTab.triggered.connect(self._openBookmarkInNewTab)
        actNewWindow.triggered.connect(self._openBookmarkInNewWindow)
        actNewPrivateWindow.triggered.connect(self._openBookmarkInNewPrivateWindow)
        actDelete.triggered.connect(self._deleteBookmarks)

        canBeDeleted = False
        items = self.ui.tree.selectedBookmarks()

        for item in items:
            if self._bookmarks.canBeModified(item):
                canBeDeleted = True
                break

        if not canBeDeleted:
            actDelete.setDisabled(True)

        selectedBookmark = self.ui.tree.selectedBookmark()
        if not selectedBookmark or not selectedBookmark.isUrl():
            actNewTab.setDisabled(True)
            actNewWindow.setDisabled(True)
            actNewPrivateWindow.setDisabled(True)

        menu.exec_(pos)
