from PyQt5.Qt import QObject
from PyQt5.Qt import Qt
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from .BookmarkItem import BookmarkItem
from mc.tools.AutoSaver import AutoSaver
from mc.app.Settings import Settings
from mc.app.DataPaths import DataPaths
from json import loads as jloads, dumps as jdumps
from mc.common.globalvars import gVar
from os.path import exists as pathexists
from os import remove
from shutil import copy
from .BookmarksModel import BookmarksModel

class Bookmarks(QObject):
    _s_bookmarksVersion = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = None  # BookmarkItem
        self._folderToolbar = None  # BookmarkItem
        self._folderMenu = None  # BookmarkItem
        self._folderUnsorted = None  # BookmarkItem
        self._lastFolder = None  # BookmarkItem

        self._model = None  # BookmarkItem
        self._autoSaver = None  # AutoSaver

        self._showOnlyIconsInToolbar = False
        self._showOnlyTextInToolbar = False

        self._autoSaver = AutoSaver(self)
        self._autoSaver.save.connect(self._saveSettings)

        self._init()
        self.loadSettings()

    def __del__(self):
        self._autoSaver.saveIfNecessary()
        del self._root

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Bookmarks')
        self._showOnlyIconsInToolbar = settings.value('showOnlyIconsInToolbar', False, type=bool)
        self._showOnlyTextInToolbar = settings.value('showOnlyTextInToolbar', False, type=bool)
        settings.endGroup()

    def showOnlyIconsInToolbar(self):
        return self._showOnlyIconsInToolbar

    def showOnlyTextInToolbar(self):
        return self._showOnlyTextInToolbar

    def rootItem(self):
        '''
        @return: BookmarkItem
        '''
        return self._root

    def toolbarFolder(self):
        '''
        @return: BookmarkItem
        '''
        return self._folderToolbar

    def menuFolder(self):
        '''
        @return: BookmarkItem
        '''
        return self._folderMenu

    def unsortedFolder(self):
        '''
        @return: BookmarkItem
        '''
        return self._folderUnsorted

    def lastUsedFolder(self):
        '''
        @return: BookmarkItem
        '''
        return self._lastFolder

    def model(self):
        '''
        @return: BookmarkItem
        '''
        return self._model

    def isBookmarked(self, url):
        '''
        @param: url QUrl
        '''
        if self.searchBookmarks(url):
            return True
        else:
            return False

    def canBeModified(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item)

        return item != self._root and \
            item != self._folderToolbar and \
            item != self._folderMenu and \
            item != self._folderUnsorted

    def searchBookmarksByUrl(self, url):
        '''
        @brief: Search bookmarks (urls only) for exact url match
        @param: url QUrl
        @return: QList<BookmarkItem*>
        '''
        items = []
        self._searchByUrl(items, self._root, url)
        return items

    def searchBookmarksByString(self, string, limit=-1, sensitive=Qt.CaseInsensitive):
        '''
        @brief: Search bookmarks for contains match through all properties
        @return: QList<BookmarkItem*>
        '''
        items = []
        self._searchByString(items, self._root, string, limit, sensitive)
        return items

    def searchKeyword(self, keyword):
        '''
        @brief: Search bookmarks for exact match of keyword
        @param: keyword QString
        @return: QList<BookmarkItem*>
        '''
        items = []
        self._searchKeyword(items, self._root, keyword)
        return items

    def addBookmark(self, parent, item):
        '''
        @param: parent BoomarkItem
        @param: item BookmarkItem
        '''
        assert(parent)
        assert(parent.isFolder())
        assert(item)

        self.insertBookmark(parent, len(parent.children()), item)

    def insertBookmark(self, parent, row, item):
        '''
        @param: parent BookmarkItem
        @param: row int
        @param: item BookmarkItem
        '''
        assert(parent)
        assert(parent.isFolder())
        assert(item)

        self._lastFolder = parent
        self._model.addBookmark(parent, row, item)
        self.bookmarkAdded.emit(item)

        self._autoSaver.changeOccurred()

    def removeBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        if not self.canBeModified(item):
            return False

        self._model.removeBookmark(item)
        self.bookmarkRemoved.emit(item)

        self._autoSaver.changeOccurred()
        return True

    def changeBookmark(self, item):
        '''
        @param: item BookmarkItem
        '''
        assert(item)
        self.bookmarkChanged.emit(item)

        self._autoSaver.changeOccurred()

    # public Q_SLOTS:
    def setShowOnlyIconsInToolbar(self, state):
        '''
        @param: state bool
        '''
        self._showOnlyIconsInToolbar = state
        self.showOnlyIconsInToolbarChanged.emit(state)
        self._autoSaver.changeOccurred()

    def setShowOnlyTextInToolbar(self, state):
        '''
        @param: state bool
        '''
        self._showOnlyTextInToolbar = state
        self.showOnlyTextInToolbarChanged.emit(state)
        self._autoSaver.changeOccurred()

    # Q_SIGNALS
    # Item was added to bookmarks
    bookmarkAdded = pyqtSignal(BookmarkItem)  # item
    # Item was removed from bookmarks
    bookmarkRemoved = pyqtSignal(BookmarkItem)  # item
    # Item data has changed
    bookmarkChanged = pyqtSignal(BookmarkItem)  # item

    showOnlyIconsInToolbarChanged = pyqtSignal(bool)  # show
    showOnlyTextInToolbarChanged = pyqtSignal(bool)  # show

    # private Q_SLOT:
    def _saveSettings(self):
        settings = Settings()
        settings.beginGroup('Bookmarks')
        settings.setValue('showOnlyIconsInToolbar', self._showOnlyIconsInToolbar)
        settings.setValue('showOnlyTextInToolbar', self._showOnlyTextInToolbar)
        settings.endGroup()

        self._saveBookmarks()

    # private:
    def _init(self):
        self._root = BookmarkItem(BookmarkItem.Root)

        self._folderToolbar = BookmarkItem(BookmarkItem.Folder, self._root)
        self._folderToolbar.setTitle(_('Bookmarks Toolbar'))
        self._folderToolbar.setDescription(_('Bookmarks located in Bookmarks Toolbar'))

        self._folderMenu = BookmarkItem(BookmarkItem.Folder, self._root)
        self._folderMenu.setTitle(_('Bookmarks Menu'))
        self._folderMenu.setDescription(_('Bookmarks located in Bookmarks Menu'))

        self._folderUnsorted = BookmarkItem(BookmarkItem.Folder, self._root)
        self._folderUnsorted.setTitle(_('Unsorted Bookmarks'))
        self._folderUnsorted.setDescription(_('All other bookmarks'))

        #if BookmarksTools.migrateBookmarksIfNecessary(self):
        #    # Bookmarks migrated just now, let's save theme ASAP
        #    self.saveBookmarks()
        #else:
        # Bookmarks don't need to be migrated, just load them as usual
        self._loadBookmarks()

        self._lastFolder = self._folderUnsorted
        self._model = BookmarksModel(self._root, self, self)

    def _loadBookmarks(self):
        bookmarksFile = DataPaths.currentProfilePath() + '/bookmarks.json'
        backupFile = bookmarksFile + '.old'
        error = False

        try:
            res = jloads(gVar.appTools.readAllFileContents(bookmarksFile))
            if type(res) != dict:
                error = True
        except ValueError:
            error = True

        if error:
            if pathexists(bookmarksFile):
                print('Warning: Bookmarks::init() Error parsing bookmarks! Using default bookmarks!')
                print('Warning: Bookmarks::init() Your bookmarks have been backed up in %s' % backupFile)

                # Backup the user bookmarks
                if pathexists(backupFile):
                    remove(backupFile)
                copy(bookmarksFile, backupFile)

            # Load default bookmarks
            content = gVar.appTools.readAllFileContents(':data/bookmarks.json')
            data = jloads(content)
            assert(type(data) == dict)

            self._loadBookmarksFromMap(data['roots'])

            # Don't forget to save the bookmarks
            self._autoSaver.changeOccurred()
        else:
            self._loadBookmarksFromMap(res['roots'])

    def _WRITE_FOLDER(self, name, folder, bookmarksMap):
        # TODO: move serialize code into BookmarkItem?
        map_ = {}
        map_['children'] = self._writeBookmarks(folder)
        map_['expanded'] = folder.isExpanded()
        map_['expanded_sidebar'] = folder.isSidebarExpanded()
        map_['name'] = folder.title()
        map_['description'] = folder.description()
        map_['type'] = 'folder'
        bookmarksMap[name] = map_

    def _saveBookmarks(self):
        bookmarksMap = {}
        self._WRITE_FOLDER('bookmark_bar', self._folderToolbar, bookmarksMap)
        self._WRITE_FOLDER('bookmark_menu', self._folderMenu, bookmarksMap)
        self._WRITE_FOLDER('other', self._folderUnsorted, bookmarksMap)

        map_ = {}
        map_['version'] = self._s_bookmarksVersion
        map_['roots'] = bookmarksMap

        data = jdumps(map_)

        if not data:
            print('Warning: Bookmarks::saveBookmarks() Error serializing bookmarks!')
            return

        fpath = DataPaths.currentProfilePath() + '/bookmarks.json'
        with open(fpath, 'wt') as fp:
            fp.write(data)

    def _READ_FOLDER(self, name, folder, map_):
        self._readBookmarks(map_[name]['children'], folder)
        folder.setExpanded(map_[name]['expanded'])
        folder.setSidebarExpanded(map_[name]['expanded_sidebar'])

    def _loadBookmarksFromMap(self, map_):
        '''
        @param: map_ QVariantMap
        '''
        self._READ_FOLDER('bookmark_bar', self._folderToolbar, map_)
        self._READ_FOLDER('bookmark_menu', self._folderMenu, map_)
        self._READ_FOLDER('other', self._folderUnsorted, map_)

    def _readBookmarks(self, list_, parent):
        '''
        @param: list_ QVariantList const
        @param: parent BookmarkItem
        '''
        assert(parent)

        for map_ in list_:
            # BookmarkItem::Type
            type_ = BookmarkItem.typeFromString(map_['type'])

            if type_ == BookmarkItem.Invalid:
                continue

            item = BookmarkItem(type_, parent)

            if type_ == BookmarkItem.Url:
                item.setUrl(QUrl.fromEncoded(map_['url'].encode()))
                item.setTitle(map_['name'])
                item.setDescription(map_['description'])
                item.setKeyword(map_['keyword'])
                item.setVisitCount(map_['visit_count'])
            elif type_ == BookmarkItem.Folder:
                item.setTitle(map_['name'])
                item.setDescription(map_['description'])
                item.setExpanded(map_['expanded'])
                item.setSidebarExpanded(map_['expanded_sidebar'])

            if 'children' in map_:
                self._readBookmarks(map_['children'], item)

    def _writeBookmarks(self, parent):
        '''
        @param: parent BookmarkItem
        @return: QVariantList
        '''
        assert(parent)

        list_ = []

        for child in parent.children():
            map_ = {}
            type_ = child.type()
            map_['type'] = BookmarkItem.typeToString(type_)

            if type_ == BookmarkItem.Url:
                map_['url'] = child.urlString()
                map_['name'] = child.title()
                map_['description'] = child.description()
                map_['keyword'] = child.keyword()
                map_['visit_count'] = child.visitCount()
            elif type_ == BookmarkItem.Folder:
                map_['name'] = child.title()
                map_['description'] = child.description()
                map_['expanded'] = child.isExpanded()
                map_['expended_sidebar'] = child.isSidebarExpanded()

            if child.children():
                map_['children'] = self._writeBookmarks(child)

            list_.append(map_)

        return list_

    def _searchByUrl(self, items, parent, url):
        '''
        @param: items QList<BookmarkItem>
        @param: parent BookmarkItem
        @param: url QUrl
        '''
        assert(items is not None)
        assert(parent)

        type_ = parent.type()
        if type_ in (BookmarkItem.Root, BookmarkItem.Folder):
            for child in parent.children():
                self._searchByUrl(items, child, url)
        elif type_ == BookmarkItem.Url:
            if parent.url() == url:
                items.append(parent)

    def _searchByString(self, items, parent, string, limit, sensitive):
        '''
        @param: items QList<BookmarkItem>
        @param: parent BookmarkItem
        @param: string QString
        @param: limit int
        @param: sensitive Qt.CaseSensitive
        '''
        assert(items is not None)
        assert(parent)

        type_ = parent.type()
        if type_ in (BookmarkItem.Root, BookmarkItem.Folder):
            for child in parent.children():
                self._searchByString(items, child, string, limit, sensitive)
        elif type_ == BookmarkItem.Url:
            if sensitive == Qt.CaseInsensitive:
                title = parent.title().lower()
                urlString = parent.urlString().lower()
                description = parent.description().lower()
                keyword = parent.keyword().lower()
                string = string.lower()
            elif sensitive == Qt.CaseSensitive:
                title = parent.title()
                urlString = parent.urlString()
                description = parent.description()
                keyword = parent.keyword()
            if string in title or \
                    string in urlString or \
                    string in description or \
                    string in keyword:
                items.append(parent)

    def _searchKeyword(self, items, parent, keyword):
        '''
        @param: items QList<BookmarkItem>
        @param: parent BookmarkItem
        @param: keyword QString
        '''
        assert(items is not None)
        assert(parent)

        type_ = parent.type()
        if type_ in (BookmarkItem.Root, BookmarkItem.Folder):
            for child in parent.children():
                self._searchKeyword(items, child, keyword)
        elif type_ == BookmarkItem.Url:
            if parent.keyword() == keyword:
                items.append(parent)
