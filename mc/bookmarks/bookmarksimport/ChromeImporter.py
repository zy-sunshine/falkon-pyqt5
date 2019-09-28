from .BookmarksImporter import BookmarksImporter
from mc.common import const
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QFileDialog
from json import loads as jloads
from json import JSONDecodeError
from mc.bookmarks.BookmarkItem import BookmarkItem
from PyQt5.Qt import QUrl

class ChromeImporter(BookmarksImporter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ''
        self._content = ''

    # override
    def description(self):
        '''
        @return: QString
        '''
        return _("Google Chrome stores its bookmarks in <b>Bookmarks</b> text file. "
            "This file is usually located in")

    # override
    def standardPath(self):
        '''
        @return: QString
        '''
        if const.OS_WIN:
            return '%APPDATA%/Chrome'
        elif const.OS_MACOS:
            return QDir.homePath() + '/Library/Application Support/Google/Chrome/'
        else:
            return QDir.homePath() + '/.config/chrome/'

    # override
    def getPath(self, parent):
        '''
        @param: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        self._path = QFileDialog.getOpenFileName(parent, _('Choose file...'),
                self.standardPath(), 'Bookmarks (Bookmarks)')

    # override
    def prepareImport(self):
        '''
        @brief: Prepare import (check if file exists, ...)
        @return: bool
        '''
        try:
            with open(self._path, 'rt') as fp:
                self._content = fp.read()
        except IOError:
            self._setError(_('Unable to open file.'))
            return False

        return True

    # override
    def importBookmarks(self):
        '''
        @brief: Import bookmarks (it must return root folder)
        '''
        try:
            jobj = jloads(self._content)
        except JSONDecodeError:
            self._setError(_('Cannot parse JSON file!'))
            return None

        if type(jobj) != map:
            self._setError(_('Invalid JSON file!'))
            return None

        rootMap = jobj['roots']
        root = BookmarkItem(BookmarkItem.Folder)
        root.setTitle('Chrome Import')

        toolbar = BookmarkItem(BookmarkItem.Folder, root)
        toolbar.setTitle(rootMap['bookmark_bar']['name'])
        self._readBookmarks(rootMap['bookmark_bar']['children'], toolbar)

        other = BookmarkItem(BookmarkItem.Folder, root)
        other.setTitle(rootMap['other']['name'])
        self._readBookmarks(rootMap['other']['children'], other)

        synced = BookmarkItem(BookmarkItem.Folder, root)
        synced.setTitle(rootMap['synced']['name'])
        self._readBookmarks(rootMap['synced']['synced'], other)

        return root

    def _readBookmarks(self, list_, parent):
        '''
        @param: list_ QVariantList
        @param: parent BookmarkItem
        '''
        assert(parent)

        for entry in list_:
            typeString = entry['type']
            if typeString == 'url':
                type_ = BookmarkItem.Url
            elif typeString == 'folder':
                type_ = BookmarkItem.Folder
            else:
                continue

            item = BookmarkItem(type_, parent)
            item.setTitle(entry['name'])

            if item.isUrl():
                item.setUrl(QUrl.fromEncoded(entry['url']))

            if 'children' in entry:
                self._readBookmarks(entry['children'], item)
