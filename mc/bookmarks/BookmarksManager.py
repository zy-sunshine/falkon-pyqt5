from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.QtWidgets import QMenu
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QIcon
from mc.bookmarks.BookmarksTools import BookmarksTools
from mc.bookmarks.BookmarkItem import BookmarkItem
from PyQt5.Qt import QUrl
from PyQt5.Qt import QTextCursor
from PyQt5.Qt import QTimer
from mc.common.globalvars import gVar
from PyQt5.Qt import Qt

class BookmarksManager(QWidget):
    def __init__(self, window, parent):
        '''
        @param: window BrowserWindow
        @param: parent QWidget
        '''
        self._ui = uic.loadUi('mc/bookmarks/BookmarksManager.ui')
        self._window = window  # QPointer<BrowserWindow>

        self._bookmarks = None  # Bookmarks
        self._selectedBookmark = None  # BookmarkItem
        self._blockDescriptionChangedSignal = False
        self._adjustHeaderSizesOnShow = False

    def setMainWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        if window:
            self._window = window

    # public Q_SLOTS:
    def search(self, string):
        self._ui.tree.search(string)

    # private Q_SLOTS:
    def _bookmarkActivated(self, item):
        '''
        @param: item BookmarkItem
        '''
        self._openBookmark(item)

    def _bookmarkCtrlActivated(self, item):
        '''
        @param: item BookmarkItem
        '''
        self._openBookmarkInNewTab(item)

    def _bookmarkShiftActivated(self, item):
        '''
        @param: item BookmarkItem
        '''
        self._openBookmarkInNewWindow(item)

    def _bookmarksSelected(self, items):
        '''
        @param: items QList<BookmarkItem>
        '''
        if len(items) != 1:
            self._selectedBookmark = None
            self._updateEditBox(None)
        else:
            self._selectedBookmark = items[0]
            self._updateEditBox(self._selectedBookmark)

    def _createContextMenu(self, pos):
        '''
        @param: pos QPoint
        '''
        menu = QMenu()
        actNewTab = menu.addAction(IconProvider.newTabIcon(), _('Open in new tab'))
        actNewWindow = menu.addAction(IconProvider.newWindowIcon(), _('Open in new window'))
        actNewPrivateWindow = menu.addAction(IconProvider.privateBrowsingIcon(), _('Open in new private window'))

        menu.addSeparator()
        actNewBookmark = menu.addAction(_('New Bookmark'), self._addBookmark)
        actNewFolder = menu.addAction(_('New Folder'), self._addFolder)
        actNewSeparator = menu.addAction(_('New Separator'), self._addSeparator)
        menu.addSeparator()
        actDelete = menu.addAction(QIcon.fromTheme('edit-delete'), _('Delete'))

        actNewTab.triggered.connect(self._openBookmarkInNewTab)
        actNewWindow.triggered.connect(self._openBookmarkInNewWindow)
        actNewPrivateWindow.triggered.connect(self._openBookmarkInNewPrivateWindow)
        actDelete.triggered.connect(self._deleteBookmarks)

        canBeDelete = False
        # QList<BookmarkItem>
        items = self._ui.tree.selectedBookmarks()
        for item in items:
            if self._bookmarks.canBeModified(item):
                canBeDelete = True
                break

        if not canBeDelete:
            actDelete.setDisabled(True)

        if not self._selectedBookmark or not self._selectedBookmark.isUlr():
            actNewTab.setDisabled(True)
            actNewWindow.setDisabled(True)
            actNewPrivateWindow.setDisabled(True)

        if not self._selectedBookmark:
            actNewBookmark.setDisabled(True)
            actNewFolder.setDisabled(True)
            actNewSeparator.setDisabled(True)

        menu.exec_(pos)

    def _openBookmark(self, item=None):
        '''
        @param: item BookmarkItem
        '''
        item = item and item or self._selectedBookmark
        BookmarksTools.openBookmark(self._getWindow(), item)

    def _openBookmarkInNewTab(self, item=None):
        '''
        @param: item BookmarkItem
        '''
        item = item and item or self._selectedBookmark
        BookmarksTools.openBookmarkInNewTab(self._getWindow(), item)

    def _openBookmarkInNewWindow(self, item=None):
        '''
        @param: item BookmarkItem
        '''
        item = item and item or self._selectedBookmark
        BookmarksTools.openBookmarkInNewWindow(self._getWindow(), item)

    def _openBookmarkInNewPrivateWindow(self, item=None):
        '''
        @param: item BookmarkItem
        '''
        item = item and item or self._selectedBookmark
        BookmarksTools.openBookmarkInNewPrivateWindow(self._getWindow(), item)

    def _addBookmark(self):
        item = BookmarkItem(BookmarkItem.Url)
        item.setTitle(_('New Bookmark'))
        item.setUrl(QUrl('http://'))
        self.__addBookmark(item)

    def _addFolder(self):
        item = BookmarkItem(BookmarkItem.Folder)
        item.setTitle(_('New Folder'))
        self.__addBookmark(item)

    def _addSeparator(self):
        item = BookmarkItem(BookmarkItem.Separator)
        self.__addBookmark(item)

    def _deleteBookmarks(self):
        items = self._ui.tree.selectedBookmarks()

        for item in items:
            if self._bookmarks.canBeModified(item):
                self._bookmarks.removeBookmark(item)

    def _bookmarkEdited(self):
        assert(len(self._ui.tree.selectedBookmarks()) == 1)

        item = self._ui.tree.selectedBookmarks()[0]
        item.setTitle(self._ui.title.text())
        item.setUrl(QUrl.fromEncoded(self._ui.address.text()))
        item.setKeyword(self._ui.keyword().text())
        item.setDescription(self._ui.description.toPlainText())

        self._bookmarks.changeBookmark(item)

    def _descriptionEdited(self):
        # There is no textEdited() signal in QPlainTextEdit
        # textChange() is emitted also when text is changed programatically
        if not self._blockDescriptionChangedSignal:
            self._bookmarkEdited()

    def _enableUpdates(self):
        self.setUpdatesEnabled(True)

    # private:
    def _updateEditBox(self, item):
        '''
        @param: item BookmarkItem
        '''
        self.setUpdatesEnabled(False)
        self._blockDescriptionChangedSignal = True

        editable = self._bookmarkEditable(item)
        showAddressAndKeyword = item and item.isUrl()

        if not item:
            self._ui.title.clear()
            self._ui.address.clear()
            self._ui.keyword.clear()
            self._ui.description.clear()
        else:
            self._ui.title.setText(item.title())
            self._ui.address.setText(item.url().toEncoded())
            self._ui.keyword.setText(item.keyword())
            self._ui.description.setPlainText(item.description())

            self._ui.title.setCursorPosition(0)
            self._ui.address.setCursorPosition(0)
            self._ui.keyword.setCursorPosition(0)
            self._ui.description.moveCursor(QTextCursor.Start)

        self._ui.title.setReadOnly(not editable)
        self._ui.address.setReadOnly(not editable)
        self._ui.keyword.setReadOnly(not editable)
        self._ui.description.setReadOnly(not editable)

        self._ui.labelAddress.setVisible(showAddressAndKeyword)
        self._ui.address.setVisible(showAddressAndKeyword)
        self._ui.labelKeyword.setVisible(showAddressAndKeyword)
        self._ui.keyword.setVisible(showAddressAndKeyword)

        # Without removing widgets from layout, there is unwanted extra spacing
        # QFormLayout l
        layout = self._ui.editBox.layout()

        if showAddressAndKeyword:
            # Show Address + Keyword
            layout.insertRow(1, self._ui.labelAddress, self._ui.address)
            layout.insertRow(2, self._ui.labelkeyword, self._ui.keyword)
        else:
            # Hide Address + Keyword
            layout.removeWidget(self._ui.labelAddress)
            layout.removeWidget(self._ui.labelKeyword)
            layout.removeWidget(self._ui.address)
            layout.removeWidget(self._ui.keyword)

        self._blockDescriptionChangedSignal = False

        # Prevent flickering
        QTimer.singleShot(10, self._enableUpdates)

    def _bookmarkEditable(self, item):
        '''
        @param: item BookmarkItem
        '''
        return item and (item.isFolder() or item.isUrl()) and self._bookmarks.canBeModified(item)

    def __addBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        parent = self._parentForNewBookmark()
        assert(parent)

        row = 0
        if self._selectedBookmark.isUrl() or self._selectedBookmark.isSeparator():
            row = self._bookmarks.model().index(self._selectedBookmark).row()
        self._bookmarks.insertBookmark(parent, row, item)

        # Select newly added bookmark
        self._ui.tree.selectBookmark(item)
        self._ui.tree.ensureBookmarkVisible(item)

        # Start editing title
        if not item.isSeparator():
            self._ui.title.setFocus()
            self._ui.title.selectAll()

    def _parentForNewBookmark(self):
        '''
        @return: BookmarkItem
        '''
        if self._selectedBookmark and self._selectedBookmark.isFolder():
            return self._selectedBookmark

        if not self._selectedBookmark or self._selectedBookmark.parent() == self._bookmarks.rootItem():
            return self._bookmarks.unsortedFolder()

        return self._selectedBookmark.parent()

    def _getWindow(self):
        '''
        @return: BrowserWindow
        '''
        if not self._window:
            self._window = gVar.app.getWindow()

        return self._window

    # override
    def showEvent(self, event):
        '''
        @param: event QShowEvent
        '''
        super().showEvent(event)

        if self._adjustHeaderSizesOnShow:
            self._ui.tree.header().resizeSection(0, self._ui.tree.header().width() / 1.9)
            self._adjustHeaderSizesOnShow = False

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QkeyEvent
        '''
        if event.key() == Qt.Key_Delete:
            self._deleteBookmarks()

        super().keyPressEvent(event)
