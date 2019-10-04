from PyQt5.QtWidgets import QBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QPushButton
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QAction
from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import QFontMetrics
from PyQt5.Qt import Qt
from mc.tools.IconProvider import IconProvider
from mc.tools.EnhancedMenu import Menu, Action
from mc.common.globalvars import gVar
from mc.common import const
from .BookmarkItem import BookmarkItem

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
        assert(window)

        if not item or not item.isUrl():
            return

        item.updateVisitCount()
        window.loadAddress(item.url())

    @classmethod
    def openBookmarkInNewTab(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        assert(window)

        if not item:
            return

        if item.isFolder():
            cls.openFolderInTabs(window, item)
        elif item.isUrl():
            item.updateVisitCount()
            window.tabWidget().addViewByUrlTitle(item.url(), item.title(),
                    gVar.appSettings.newTabPosition)

    @classmethod
    def openBookmarkInNewWindow(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        if not item.isUrl():
            return

        item.updateVisitCount()
        gVar.app.createWindow(const.BW_NewWindow, item.url())

    @classmethod
    def openBookmarkInNewPrivateWindow(cls, window, item):
        '''
        @param: window BrowserWindow
        @param: item BookmarkItem
        '''
        if not item.isUrl():
            return

        item.updateVisitCount()
        gVar.app.startPrivateBrowsing(item.url())

    @classmethod
    def openFolderInTabs(cls, window, folder):
        '''
        @param: window BrowserWindow
        @param: folder BookmarkItem
        '''
        assert(window)
        assert(folder.isFolder())

        showWarning = len(folder.children()) > 10
        if not showWarning:
            for child in folder.children():
                if child.isFolder():
                    showWarning = True
                    break

        if showWarning:
            button = QMessageBox.warning(window, _('Confirmation'),
                _('Are you sure you want to open all bookmarks from "%s" folder in tabs?') % folder.title(),
                QMessageBox.Yes | QMessageBox.No)
            if button != QMessageBox.Yes:
                return

        for child in folder.children():
            if child.isUrl():
                cls.openBookmarkInNewTab(window, child)
            elif child.isFolder():
                cls.openFolderInTabs(window, child)

    @classmethod
    def addActionToMenu(cls, receiver, menu, item):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: item BookmarkItem
        '''
        assert(menu)
        assert(item)

        type_ = item.type()
        if type_ == BookmarkItem.Url:
            cls.addUrlToMenu(receiver, menu, item)
        elif type_ == BookmarkItem.Folder:
            cls.addFolderToMenu(receiver, menu, item)
        elif type_ == BookmarkItem.Separator:
            cls.addSeparatorToMenu(menu, item)

    @classmethod
    def addFolderToMenu(cls, receiver, menu, folder):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: folder BookmarkItem
        '''
        assert(menu)
        assert(folder)
        assert(folder.isFolder())

        subMenu = Menu(menu)
        title = QFontMetrics(subMenu.font()).elidedText(folder.title(), Qt.ElideRight, 250)
        subMenu.setTitle(title)
        subMenu.setIcon(folder.icon())

        cls.addFolderContentsToMenu(receiver, subMenu, folder)

        # QAction
        act = menu.addMenu(subMenu)
        act.setData(folder)
        act.setIconVisibleInMenu(True)

    @classmethod
    def addUrlToMenu(cls, receiver, menu, bookmark):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: bookmark BookmarkItem
        '''
        assert(menu)
        assert(bookmark)
        assert(bookmark.isUrl())

        act = Action(menu)
        title = QFontMetrics(act.font()).elidedText(bookmark.title(), Qt.ElideRight, 250)
        act.setText(title)
        act.setData(bookmark)
        act.setIconVisibleInMenu(True)

        act.triggered.connect(receiver._bookmarkActivated)
        act.ctrlTriggered.connect(receiver._bookmarkCtrlActivated)
        act.shiftTriggered.connect(receiver._bookmarkShiftActivated)

        menu.addAction(act)

    @classmethod
    def addSeparatorToMenu(cls, menu, separator):
        '''
        @param: menu Menu
        @param: separator BookmarkItem
        '''
        assert(menu)
        assert(separator.isSeparator())

        menu.addSeparator()

    @classmethod
    def addFolderContentsToMenu(cls, receiver, menu, folder):
        '''
        @param: receiver QObject
        @param: menu Menu
        @param: folder BookmarkItem
        '''
        menu.aboutToShow.connect(receiver._menuAboutToShow)
        menu.menuMiddleClicked.connect(receiver._menuMiddleClicked)

        for child in folder.children():
            cls.addActionToMenu(receiver, menu, child)

        if menu.isEmpty():
            menu.addAction(_('Empty')).setDisabled(True)

    #@classmethod
    #def migrateBookmarksIfNecessary(cls, bookmarks):
    #    '''
    #    @brief: Migration from Sql Bookmarks (returns tree if bookmarks migrated)
    #    '''
    #    pass
