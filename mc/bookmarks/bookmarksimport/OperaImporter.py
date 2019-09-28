from .BookmarksImporter import BookmarksImporter
from PyQt5.Qt import QTextStream
from PyQt5.Qt import QFile
from mc.common import const
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QFileDialog
from mc.bookmarks.BookmarkItem import BookmarkItem
from PyQt5.Qt import QUrl

class OperaImporter(BookmarksImporter):
    # enum Token
    _EmptyLine = 0
    _StartFolder = 1
    _EndFolder = 2
    _StartUrl = 3
    _StartSeparator = 4
    _StartDeleted = 5
    _KeyValuePair = 6
    _Invalid = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self._key = ''
        self._value = ''
        self._path = ''
        self._file = QFile()
        self._stream = QTextStream()
        self._lines = []

    # override
    def description(self):
        '''
        @return: QString
        '''
        return _("Opera stores its bookmarks in <b>bookmarks.adr</b> text file. "
            "This file is usually located in")

    # override
    def standardPath(self):
        '''
        @return: QString
        '''
        if const.OS_WIN:
            return '%APPDATA%/Opera/'
        else:
            return QDir.homePath() + '/.opera/'

    # override
    def getPath(self, parent):
        '''
        @param: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        self._path = QFileDialog.getOpenFileName(parent, _('Choose file...'),
                self.standardPath(), 'Bookmarks (*.adr)')
        return self._path

    # override
    def prepareImport(self):
        '''
        @brief: Prepare import (check if file exists, ...)
        @return: bool
        '''
        try:
            with open(self._path, 'rt') as fp:
                self._lines = fp.readlines()
        except IOError:
            self._setError(_('Unable to open file.'))
            return False

        if len(self._lines) < 2:
            self._setError(_('Invalid format!'))
            return False

        if self._lines.pop(0) != 'Opera Hotlist version 2.0':
            self._setError(_('File is not valid Opera bookmarks file!'))
            return False

        if not self._lines.pop(0).startswith('Options: encoding = utf8'):
            self._setError(_('Only UTF-8 encoded Opera bookmarks file is supported!'))
            return False

        return True

    # override
    def importBookmarks(self):  # noqa C901
        '''
        @brief: Import bookmarks (it must return root folder)
        '''
        root = BookmarkItem(BookmarkItem.Folder)
        root.setTitle('Opera Import')

        folders = []  # QList<BookmarkItem>
        folders.append(root)

        def getParent():
            if folders:
                return folders[-1]
            else:
                return root

        item = None  # BookmarkItem
        while self._lines:
            res = self._parseLine(self._lines.pop(0))
            if res == self._StartFolder:
                item = BookmarkItem(BookmarkItem.Folder, getParent())
                while self._lines:
                    tok = self._parseLine(self._lines.pop(0))
                    if tok == self._EmptyLine:
                        break
                    elif tok == self._KeyValuePair and self._key == 'NAME':
                        item.setTitle(self._value)
                folders.append(item)
            elif res == self._EndFolder:
                if len(folders) > 0:
                    folders.pop(-1)
            elif res == self._StartUrl:
                item = BookmarkItem(BookmarkItem.Url, getParent())
                while self._lines:
                    tok = self._parseLine(self._lines.pop(0))
                    if tok == self._EmptyLine:
                        break
                    elif tok == self._KeyValuePair:
                        if self._key == 'NAME':
                            item.setTitle(self._value)
                        elif self._key == 'URL':
                            item.setUrl(QUrl(self._value))
                        elif self._key == 'DESCRIPTION':
                            item.setDescription(self._value)
                        elif self._key == 'SHORT NAME':
                            item.setKeyword(self._value)
            elif res == self._StartSeparator:
                item = BookmarkItem(BookmarkItem.Separator, getParent())
                while self._lines:
                    if self._parseLine(self._lines.pop(0)) == self._EmptyLine:
                        break
            elif res == self._StartDeleted:
                while self._lines:
                    if self._parseLine(self._lines.pop(0)) == self._EmptyLine:
                        break

        return root

    def _parseLine(self, line):
        '''
        @param: line QString
        '''
        line = line.strip()

        if not line:
            return self._EmptyLine

        if line == '#FOLDER':
            return self._StartFolder

        if line == '-':
            return self._EndFolder

        if line == '#URL':
            return self._StartUrl

        if line == '#SEPERATOR':
            return self._StartSeparator

        if line == '#DELETED':
            return self._StartDeleted

        index = line.find('=')

        # Let's assume "key=" is valid line with empty value (but not ="value")
        if index > 0:
            self._key = line[0:index]
            self._value = line[index+1:]
            return self._KeyValuePair

        return self._Invalid
