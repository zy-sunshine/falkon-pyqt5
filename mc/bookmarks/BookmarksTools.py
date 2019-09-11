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
        pass

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
