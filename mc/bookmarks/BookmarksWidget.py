from PyQt5 import uic
from PyQt5.Qt import QIcon
from PyQt5.Qt import QApplication
from PyQt5.Qt import QTimer
from mc.navigation.LocationBarPopup import LocationBarPopup
from mc.common.globalvars import gVar
from .BookmarkItem import BookmarkItem

class BookmarksWidget(LocationBarPopup):
    HIDE_DELAY = 270
    def __init__(self, view, bookmark, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/bookmarks/BookmarksWidget.ui', self)
        self._view = view
        self._bookmark = bookmark

        self._bookmarks = gVar.app.bookmarks()  # Bookmarks
        self._speedDial = gVar.app.plugins().speedDial()  # SpeedDial
        self._edited = False

        self._ui.bookmarksButton.setIcon(QIcon.fromTheme('bookmark-new'))

        self._init()

    # private Q_SLOTS:
    def _toggleSpeedDial(self):
        # SpeedDial::Page
        page = self._speedDial.pageForUrl(self._view.url())

        if not page.url:
            self._speedDial.addPage(self._view.url(), self._view.title())
        else:
            self._speedDial.removePage(page)

        self._closePopup()

    def _toggleBookmark(self):
        if self._bookmark:
            if self._edited:
                # Change folder
                self._bookmarks.removeBookmark(self._bookmark)
                self._bookmarks.addBookmark(self._ui.folderButton.selectedFolder(), self._bookmark)
            else:
                self._bookmarks.removeBookmark(self._bookmark)
        else:
            # Save bookmark
            bookmark = BookmarkItem(BookmarkItem.Url)
            bookmark.setTitle(self._view.title())
            bookmark.setUrl(self._view.url())
            self._bookmarks.addBookmark(self._ui.folderButton.selectedFolder(), bookmark)

        self._closePopup()

    def _bookmarkEdited(self):
        if self._edited:
            return

        self._edited = True
        self._ui.bookmarksButton.setText(_('Update Bookmark'))
        self._ui.bookmarksButton.setFlat(True)

    # private:
    def _init(self):
        # The locationbar's direction is direction of its text,
        # it dynamically changes and so, it's not good choice for this widget.
        self.setLayoutDirection(QApplication.layoutDirection())

        # Init SpeedDial button
        # SpeedDial::Page
        page = self._speedDial.pageForUrl(self._view.url())
        if not page.url:
            self._ui.speeddialButton.setFlat(True)
            self._ui.speeddialButton.setText(_('Add to Speed Dial'))
        else:
            self._ui.speeddialButton.setFlat(False)
            self._ui.speeddialButton.setText(_('Remove from Speed Dial'))

        # Init Bookmarks button
        if self._bookmark:
            self._ui.bookmarksButton.setText(_('Remove from Bookmarks'))
            self._ui.bookmarksButton.setFlat(False)

            assert(self._bookmark.parent())
            self._ui.folderButton.setSelectedFolder(self._bookmark.parent())
            self._ui.folderButton.selectedFolderChanged.connect(self._bookmarkEdited)

        self._ui.speeddialButton.clicked.connect(self._toggleSpeedDial)
        self._ui.bookmarksButton.clicked.connect(self._toggleBookmark)

    def _closePopup(self):
        # Prevent clicking again on buttons while popup is being closed
        self._ui.speeddialButton.clicked.disconnect(self._toggleSpeedDial)
        self._ui.bookmarksButton.clicked.disconnect(self._toggleBookmark)

        QTimer.singleShot(self.HIDE_DELAY, self.close)
