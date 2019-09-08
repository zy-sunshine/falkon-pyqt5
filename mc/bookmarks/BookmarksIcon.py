from mc.tools.ClickableLabel import ClickableLabel
from PyQt5.Qt import QUrl
from PyQt5.Qt import Qt
from mc.common.globalvars import gVar

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
        # TODO:
        #gVar.app.plugins().speedDial().pagesChanged.connect(self._speedDialChanged)

        self.clicked.connect(self._iconClicked)

    def setWebView(self, view):
        pass

    def checkBookmark(self, url, forceCheck=False):
        pass

    # private Q_SLOTS:
    def _bookmarksChanged(self):
        pass

    def _speedDialChanged(self):
        pass

    def _iconClicked(self):
        pass

    # private:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass

    # override
    def mousePressEvent(self, event):
        pass

    def _setBookmarkSaved(self):
        pass

    def _setBookmarkDisabled(self):
        pass
