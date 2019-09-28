import peewee
from .BookmarksImporter import BookmarksImporter
from mc.common import const
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QFileDialog
from os.path import exists as pathexists
from PyQt5.Qt import QUrl
from mc.bookmarks.BookmarkItem import BookmarkItem

class MozBookmarks(peewee.Model):
    class Meta:
        db_table = 'moz_bookmarks'
    id = peewee.AutoField(primary_key=True)
    parent = peewee.IntegerField()
    type = peewee.IntegerField()
    title = peewee.TextField()
    fk = peewee.IntegerField()

class MozPlaces(peewee.Model):
    class Meta:
        db_table = 'moz_places'
    id = peewee.AutoField(primary_key=True)
    url = peewee.TextField()

class FirefoxImporter(BookmarksImporter):
    # enum Type
    _Url = 0
    _Folder = 1
    _Separator = 2
    _Invalid = 3

    class _Item:
        def __init__(self):
            self.id = 0
            self.parent = 0
            self.type = 3
            self.title = ''
            self._url = QUrl()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ''
        self._db = None  # Database Connection

    # override
    def description(self):
        '''
        @return: QString
        '''
        return _("Mozilla Firefox stores its bookmarks in <b>places.sqlite</b> SQLite "
            "database. This file is usually located in")

    # override
    def standardPath(self):
        '''
        @return: QString
        '''
        if const.OS_WIN:
            return '%APPDATA%/Mozilla/'
        else:
            return QDir.homePath() + '/.mozilla/firefox/'

    # override
    def getPath(self, parent):
        '''
        @param: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        self._path = QFileDialog.getOpenFileName(parent, _('Choose file...'),
                self.standardPath(), 'Places (places.sqlite)')
        return self._path

    # override
    def prepareImport(self):
        '''
        @note: Make sure this connection is properly closed if already opened
        @brief: Prepare import (check if file exists, ...)
        @return: bool
        '''

        if not pathexists(self._path):
            self._setError(_('File does not exists.'))
            return False

        if self._db:
            self._db.close()
        self._db = peewee.SqliteDatabase(self._path)
        try:
            self._db.connect()
        except peewee.DatabaseError:
            self._setError(_('Unable to open database. If Firefox running?'))
            return False

        return True

        MozBookmarks._meta.database = self._db

    # override
    def importBookmarks(self):
        root = BookmarkItem(BookmarkItem.Folder)
        root.setTitle('Firefox Import')

        try:
            items = self._importBookmarks()
        except peewee.DatabaseError as e:
            self._setError(str(e))

        hash_ = {}  # QHash<int, BookmarkItem>
        for item in items:
            parent = hash_.get(item.parent)
            bookmark = BookmarkItem(item.type, parent and parent or root)
            bookmark.setTitle(item.title and item.title or item.url.toString())
            bookmark.setUrl(item.url)

            hash_[item.id] = bookmark

        return root

    def _importBookmarks(self):
        '''
        @brief: Import bookmarks (it must return root folder)
        '''
        items = []  # QList<Item>

        dbobjs = MozBookmarks.select().where(MozBookmarks.fk.is_null(False) | MozBookmarks.type == 3)

        for dbobj in dbobjs:
            item = self._Item()
            item.id = dbobj.id
            item.parent = dbobj.parent
            item.type = self._typeFromValue(dbobj.type)
            item.title = dbobj.title
            fk = dbobj.fk

            if item.type == BookmarkItem.Invalid:
                continue

            urlDbobj = MozPlaces.select().where(MozPlaces.id==fk).first()
            if urlDbobj:
                item.url = QUrl(urlDbobj.url)

            if item.url.scheme() == 'place':
                continue

            items.append(item)

    def _typeFromValue(self, value):
        '''
        @return: BookmarkItem::Type
        '''
        if value == 1:
            return BookmarkItem.Url
        elif value == 2:
            return BookmarkItem.Folder
        elif value == 3:
            return BookmarkItem.Separator
        else:
            return BookmarkItem.Invalid
