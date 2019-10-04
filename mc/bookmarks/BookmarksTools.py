from PyQt5.QtWidgets import QBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QPushButton
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QAction
from mc.tools.IconProvider import IconProvider
from .BookmarkItem import BookmarkItem
from mc.common.globalvars import gVar

class BookmarksFoldersMenu(QMenu):
    def __init__(self, parent=None):
        '''
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._selectedFolder = None  # BookmarkItem
        self._init()

    def selectedFolder(self):
        '''
        @return: BookmarkItem
        '''
        return self._selectedFolder

    # Q_SIGNALS:
    folderSelected = pyqtSignal(BookmarkItem)

    # private Q_SLOTS:
    def _folderChoosed(self):
        act = self.sender()
        if not isinstance(act, QAction):
            return
        folder = act.data()
        if not isinstance(folder, BookmarkItem):
            return
        self.folderSelected.emit(folder)

    def _ADD_MENU(self, name):
        bookmarks = gVar.app.bookmarks()
        item = getattr(bookmarks, name)()
        menu = self.addMenu(item.icon(), item.title())
        self._createMenu(menu, item)

    # private:
    def _init(self):
        self._ADD_MENU('toolbarFolder')
        self._ADD_MENU('menuFolder')
        self._ADD_MENU('unsortedFolder')

    def _createMenu(self, menu, parent):
        '''
        @param: menu QMenu
        @param: parent BookmarkItem
        '''
        act = menu.addAction(_('Choose %s') % parent.title())
        act.setData(parent)
        act.triggered.connect(self._folderChoosed)

        menu.addSeparator()

        for child in parent.children():
            if not child.isFolder(): continue
            m = menu.addMenu(child.icon(), child.title())
            self._createMenu(m, child)

class BookmarksFoldersButton(QPushButton):
    def __init__(self, parent, folder=None):
        '''
        @param: parent QWidget
        @param: folder BookmarkItem
        '''
        super().__init__(parent)
        self._menu = BookmarksFoldersMenu(self)  # BookmarksFoldersMenu
        self._selectedFolder = None  # BookmarkItem
        if folder:
            self._selectedFolder = folder
        else:
            self._selectedFolder = gVar.app.bookmarks().lastUsedFolder()
        self._init()
        self._menu.folderSelected.connect(self.setSelectedFolder)

    def selectedFolder(self):
        '''
        @return: BookmarkItem
        '''
        return self._selectedFolder

    # Q_SIGNALS:
    selectedFolderChanged = pyqtSignal(BookmarkItem)

    # public Q_SLOTS:
    def setSelectedFolder(self, folder):
        '''
        @param: folder BookmarkItem
        '''
        assert(folder)
        assert(folder.isFolder())

        self._selectedFolder = folder
        self.setText(folder.title())
        self.setIcon(folder.icon())

        if self.sender():
            self.selectedFolderChanged.emit(folder)

    def _init(self):
        self.setMenu(self._menu)
        self.setSelectedFolder(self._selectedFolder)

class BookmarksTools(object):
    @classmethod
    def addBookmarkDialog(cls, parent, url, title, folder=None):
        '''
        @brief: Add Bookmark Dialogs
        @param: parent QWidget
        @param: url QUrl
        @param: title QString
        @param: folder BookmarkItem
        '''
        dialog = QDialog(parent)
        layout = QBoxLayout(QBoxLayout.TopToBottom, dialog)
        label = QLabel(dialog)
        edit = QLineEdit(dialog)
        folderButton = BookmarksFoldersButton(dialog, folder)

        box = QDialogButtonBox(dialog)
        box.addButton(QDialogButtonBox.Ok)
        box.addButton(QDialogButtonBox.Cancel)
        box.rejected.connect(dialog.reject)
        box.accepted.connect(dialog.accept)

        layout.addWidget(label)
        layout.addWidget(edit)
        layout.addWidget(folderButton)
        layout.addWidget(box)

        label.setText(_('Choose name and location of this bookmark.'))
        edit.setText(title)
        edit.setCursorPosition(0)
        dialog.setWindowIcon(IconProvider.iconForUrl(url))
        dialog.setWindowTitle(_('Add New Bookmark'))

        size = dialog.size()
        size.setWidth(350)
        dialog.resize(size)
        dialog.exec_()

        if dialog.result() == QDialog.Rejected or not edit.text():
            del dialog
            return False

        bookmark = BookmarkItem(BookmarkItem.Url)
        bookmark.setTitle(edit.text())
        bookmark.setUrl(url)
        gVar.app.bookmarks().addBookmark(folderButton.selectedFolder(), bookmark)

        del dialog
        return True

    @classmethod
    def bookmarkAllTabsDialog(cls, parent, tabWidget, folder=None):
        '''
        @param: parent QWidget
        @param: tabWidget TabWidget
        @param: folder BookmarkItem
        '''
        pass

    @classmethod
    def editBookmarkDialog(cls, parent, item):
        '''
        @param: parent QWidget
        @param: item BookmarkItem
        '''
        pass

    @classmethod
    def openBookmark(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        pass

    @classmethod
    def openBookmarkInNewTab(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        pass

    @classmethod
    def openBookmarkInNewWindow(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        pass

    @classmethod
    def openBookmarkInNewPrivateWindow(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        pass

    @classmethod
    def openFolderInTabs(cls, window, folder):
        '''
        @param: window BrowserWindow
        @param: folder BookmarkItem
        '''
        pass

    @classmethod
    def addActionToMenu(cls, receiver, menu, item):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: item BookmarkItem
        '''
        pass

    @classmethod
    def addFolderToMenu(cls, receiver, menu, folder):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: folder BookmarkItem
        '''
        pass

    @classmethod
    def addUrlToMenu(cls, receiver, menu, bookmark):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: bookmark BookmarkItem
        '''
        pass

    @classmethod
    def addSeparatorToMenu(cls, menu, folder):
        '''
        @param: menu Menu
        @param: separator BookmarkItem
        '''
        pass

    @classmethod
    def addFolderContentsToMenu(cls, receiver, menu, folder):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: folder BookmarkItem
        '''
        pass

    #@classmethod
    #def migrateBookmarksIfNecessary(cls, bookmarks):
    #    '''
    #    @brief: Migration from Sql Bookmarks (returns tree if bookmarks migrated)
    #    '''
    #    pass
