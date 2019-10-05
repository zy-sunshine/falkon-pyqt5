from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QPoint
from PyQt5.Qt import Qt
from PyQt5.Qt import QHBoxLayout
from PyQt5.Qt import QStyle
from PyQt5.Qt import QTimer
from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import QIcon
from PyQt5.Qt import QRect
from PyQt5.Qt import QUrl
from mc.common.globalvars import gVar
from .BookmarksTools import BookmarksTools
from mc.tools.IconProvider import IconProvider
from .BookmarksToolbarButton import BookmarksToolbarButton
from .BookmarksModel import BookmarksButtonMimeData
from .BookmarkItem import BookmarkItem

class BookmarksToolbar(QWidget):
    def __init__(self, window, parent=None):
        '''
        @param: window BrowserWindow
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._window = window
        self._bookmarks = gVar.app.bookmarks()  # Bookmarks
        self._clickedBookmark = None  # BookmarkItem
        self._layout = None  # QHBoxLayout
        self._updateTimer = None  # QTimer
        self._actShowOnlyIcons = None  # QAction
        self._actShowOnlyText = None  # QAction

        self._dropRow = -1
        self._dropPos = QPoint()

        self.setObjectName('bookmarksbar')
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self._layout = QHBoxLayout(self)
        margin = self.style().pixelMetric(QStyle.PM_ToolBarItemMargin, None, self) + \
            self.style().pixelMetric(QStyle.PM_ToolBarFrameWidth, None, self)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(self.style().pixelMetric(QStyle.PM_ToolBarItemSpacing, None, self))
        self.setLayout(self._layout)

        self._updateTimer = QTimer(self)
        self._updateTimer.setInterval(300)
        self._updateTimer.setSingleShot(True)
        self._updateTimer.timeout.connect(self._refresh)

        self._bookmarks.bookmarkAdded.connect(self._bookmarksChanged)
        self._bookmarks.bookmarkRemoved.connect(self._bookmarksChanged)
        self._bookmarks.bookmarkChanged.connect(self._bookmarksChanged)
        self._bookmarks.showOnlyIconsInToolbarChanged.connect(self._showOnlyIconsChanged)
        self._bookmarks.showOnlyTextInToolbarChanged.connect(self._showOnlyTextChanged)
        self.customContextMenuRequested.connect(self._contextMenuRequested)

        self._refresh()

    # private Q_SLOTS:
    def _contextMenuRequested(self, pos):
        '''
        @param: pos QPoint
        '''
        # BookmarksToolbarButton
        button = self._buttonAt(pos)
        if button:
            self._clickedBookmark = button.bookmark()
        else:
            self._clickedBookmark = None

        menu = QMenu()
        actNewTab = menu.addAction(IconProvider.newTabIcon(), _('Open in new tab'))
        actNewWindow = menu.addAction(IconProvider.newWindowIcon(), _('Open in new window'))
        actNewPrivateWindow = menu.addAction(IconProvider.privateBrowsingIcon(), _('Open in new private window'))
        menu.addSeparator()
        actEdit = menu.addAction(_('Edit'))
        actDelete = menu.addAction(QIcon.fromTheme('edit-delete'), _('Delete'))
        menu.addSeparator()
        self._actShowOnlyIcons = menu.addAction(_('Show Only Icons'))
        self._actShowOnlyIcons.setCheckable(True)
        self._actShowOnlyIcons.setChecked(self._bookmarks.showOnlyIconsInToolbar())
        self._actShowOnlyIcons.toggled.connect(self._showOnlyIconsChanged)
        self._actShowOnlyText = menu.addAction(_('Show Only Text'))
        self._actShowOnlyText.setCheckable(True)
        self._actShowOnlyText.setChecked(self._bookmarks.showOnlyTextInToolbar())
        self._actShowOnlyText.toggled.connect(self._showOnlyTextChanged)

        actNewTab.triggered.connect(self._openBookmarkInNewTab)
        actNewWindow.triggered.connect(self._openBookmarkInNewWindow)
        actNewPrivateWindow.triggered.connect(self._openBookmarkInNewPrivateWindow)
        actEdit.triggered.connect(self._editBookmark)
        actDelete.triggered.connect(self._deleteBookmark)

        canBeModify = self._clickedBookmark and self._bookmarks.canBeModified(self._clickedBookmark)
        actEdit.setEnabled(canBeModify)
        actDelete.setEnabled(canBeModify)
        canOpen = self._clickedBookmark and self._clickedBookmark.isUrl()
        actNewTab.setEnabled(canOpen)
        actNewWindow.setEnabled(canOpen)
        actNewPrivateWindow.setEnabled(canOpen)

        menu.exec_(self.mapToGlobal(pos))

        if button:
            # Clear mouse over state after closing menu
            button.update()

        self._clickedBookmark = None
        self._actShowOnlyIcons = None
        self._actShowOnlyText = None

    def _refresh(self):
        self._clear()

        folder = gVar.app.bookmarks().toolbarFolder()

        for child in folder.children():
            self._addItem(child)

        self._layout.addStretch()

    def _bookmarksChanged(self):
        self._updateTimer.start()

    def _showOnlyIconsChanged(self, state):
        if state and self._actShowOnlyText:
            self._actShowOnlyText.setChecked(False)

        for idx in range(self._layout.count()):
            # BookmarksToolbarButton
            btn = self._layout.itemAt(idx).widget()
            if isinstance(btn, BookmarksToolbarButton):
                btn.setShowOnlyIcon(state)

    def _showOnlyTextChanged(self, state):
        if state and self._actShowOnlyIcons:
            self._actShowOnlyIcons.setChecked(False)

        for idx in range(self._layout.count()):
            # BookmarksToolbarButton
            btn = self._layout.itemAt(idx).widget()
            if isinstance(btn, BookmarksToolbarButton):
                btn.setShowOnlyText(state)

    def _openBookmarkInNewTab(self):
        if self._clickedBookmark:
            BookmarksTools.openBookmarkInNewTab(self._window, self._clickedBookmark)

    def _openBookmarkInNewWindow(self):
        if self._clickedBookmark:
            BookmarksTools.openBookmarkInNewWindow(self._clickedBookmark)

    def _openBookmarkInNewPrivateWindow(self):
        if self._clickedBookmark:
            BookmarksTools.openBookmarkInNewPrivateWindow(self._clickedBookmark)

    def _editBookmark(self):
        if self._clickedBookmark:
            BookmarksTools.editBookmarkDialog(self, self._clickedBookmark)
            self._bookmarks.changeBookmark(self._clickedBookmark)

    def _deleteBookmark(self):
        if self._clickedBookmark:
            self._bookmarks.removeBookmark(self._clickedBookmark)

    # private:
    def _clear(self):
        for idx in range(self._layout.count()):
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        assert(self._layout.isEmpty())

    def _addItem(self, item):
        '''
        @param: BookmarkItem
        '''
        assert(item)

        button = BookmarksToolbarButton(item, self)
        button.setMainWindow(self._window)
        button.setShowOnlyIcon(self._bookmarks.showOnlyIconsInToolbar())
        button.setShowOnlyText(self._bookmarks.showOnlyTextInToolbar())
        self._layout.addWidget(button)

    def _buttonAt(self, pos):
        '''
        @param: pos QPoint
        @return: BookmarksToolbarButton
        '''
        button = QApplication.widgetAt(self.mapToGlobal(pos))
        if not isinstance(button, BookmarksToolbarButton):
            button = None
        return button

    # override
    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        size.setHeight(max(20, size.height()))
        return size

    # override
    def dropEvent(self, event):
        '''
        @param: event QDropEvent
        '''
        row = self._dropRow
        self._clearDropIndicator()

        mime = event.mimeData()
        if not mime.hasUrls() and not mime.hasFormat(BookmarksButtonMimeData.mimeType()):
            super().dropEvent(event)
            return

        # BookmarkItem
        parent = self._bookmarks.toolbarFolder()
        bookmark = None

        if mime.hasFormat(BookmarksButtonMimeData.mimeType()):
            bookmarkMime = mime
            assert(isinstance(bookmarkMime, BookmarksButtonMimeData))
            bookmark = bookmarkMime.item()
            initialIndex = bookmark.parent().children().index(bookmark)
            current = self._buttonAt(self._dropPos)
            if initialIndex < self._layout.indexOf(current):
                row -= 1
        else:
            url = mime.urls()[0]
            if mime.hasText():
                title = mime.text()
            else:
                title = url.toEncoded(QUrl.RemoveScheme)

            bookmark = BookmarkItem(BookmarkItem.Url)
            bookmark.setTitle(title)
            bookmark.setUrl(url)

        if row >= 0:
            self._bookmarks.insertBookmark(parent, row, bookmark)
        else:
            self._bookmarks.addBookmark(parent, bookmark)

    # override
    def dragEnterEvent(self, event):
        '''
        @param: event QDragEnterEvent
        '''
        mime = event.mimeData()

        if (mime.hasUrls() and mime.hasText()) or mime.hasFormat(BookmarksButtonMimeData.mimeType()):
            event.acceptProposedAction()
            return

        super().dragEnterEvent(event)

    # override
    def dragMoveEvent(self, event):
        '''
        @param: event QDragMoveEvent
        '''
        eventX = event.pos().x()
        # BoomarksToolbarButton
        button = self._buttonAt(event.pos())
        self._dropPos = event.pos()
        self._dropRow = self._layout.indexOf(button)
        if button:
            if eventX - button.x() >= button.x() + button.width() - eventX:
                self._dropRow + 1
        else:
            self._dropRow = -1

        self.update()

    # override
    def dragLeaveEvent(self, event):
        '''
        @param: event QDragLeaveEvent
        '''
        self._clearDropIndicator()

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        super().paintEvent(event)

        # Draw drop indicator
        if self._dropRow != -1:
            # BookmarksToolbarButton
            button = self._buttonAt(self._dropPos)
            if button:
                if button.bookmark().isFolder():
                    return
                tmpRect = QRect(button.x(), 0, button.width(), self.height())
                rect = QRect()

                if self._dropRow == self._layout.indexOf(button):
                    rect = QRect(max(0, tmpRect.left() - 2), tmpRect.top(), 3, tmpRect.height())
                else:
                    rect = QRect(tmpRect.right() + 0, tmpRect.top(), 3, tmpRect.height())

                gVar.appTools.paintDropIndicator(self, rect)

    def _clearDropIndicator(self):
        self._dropRow = -1
        self.update()
