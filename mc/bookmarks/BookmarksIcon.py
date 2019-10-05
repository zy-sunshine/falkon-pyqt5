from mc.tools.ClickableLabel import ClickableLabel
from PyQt5.Qt import QUrl
from PyQt5.Qt import Qt
from mc.common.globalvars import gVar
from .BookmarksWidget import BookmarksWidget

class BookmarksIcon(ClickableLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._view = None  # WebView
        self._bookmark = None  # BookmarkItem
        self._lastUrl = QUrl()

        self.setObjectName('locationbar-bookmarkicon')
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(_('Bookmark this page'))
        self.setFocusPolicy(Qt.ClickFocus)

        gVar.app.bookmarks().bookmarkAdded.connect(self._bookmarksChanged)
        gVar.app.bookmarks().bookmarkRemoved.connect(self._bookmarksChanged)
        gVar.app.bookmarks().bookmarkChanged.connect(self._bookmarksChanged)
        gVar.app.plugins().speedDial().pagesChanged.connect(self._speedDialChanged)

        self.clicked.connect(self._iconClicked)

    def setWebView(self, view):
        self._view = view

        def urlChangedCb(url):
            self.checkBookmark(url)
        view.urlChanged.connect(urlChangedCb)

    def checkBookmark(self, url, forceCheck=False):
        '''
        @param: url QUrl
        '''
        if not forceCheck and self._lastUrl == url:
            return

        # QList<BookmarkItem>
        items = gVar.app.bookmarks().searchBookmarksByUrl(url)
        self._bookmark = len(items) and items[0] or None

        if self._bookmark or gVar.app.plugins().speedDial().pageForUrl(url).isValid():
            self._setBookmarkSaved()
        else:
            self._setBookmarkDisabled()

        self._lastUrl = url

    # private Q_SLOTS:
    def _bookmarksChanged(self):
        self.checkBookmark(self._lastUrl, True)

    def _speedDialChanged(self):
        self.checkBookmark(self._lastUrl, True)

    def _iconClicked(self):
        if not self._view:
            return

        widget = BookmarksWidget(self._view, self._bookmark, self.parentWidget())
        widget.showAt(self.parentWidget())

    # private:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        # Prevent propagating to LocationBar
        event.accept()

    # override
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # Prevent propagating to LocationBar
        event.accept()

    def _setBookmarkSaved(self):
        self.setProperty('bookmarked', True)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setToolTip(_('Edit this bookmark'))

    def _setBookmarkDisabled(self):
        self.setProperty('bookmarked', False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setToolTip(_('Bookmark this page'))
