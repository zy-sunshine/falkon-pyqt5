from .BookmarksImporter import BookmarksImporter
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QFileDialog
from os.path import exists as pathexists
from mc.bookmarks.BookmarkItem import BookmarkItem
from PyQt5.Qt import QSettings
from PyQt5.Qt import QUrl

class IeImporter(BookmarksImporter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ''

    # override
    def description(self):
        '''
        @return: QString
        '''
        return _("Internet Explorer stores its bookmarks in <b>Favorites</b> folder. "
            "This folder is usually located in")

    # override
    def standardPath(self):
        '''
        @return: QString
        '''
        return QDir.homePath() + '/Favorites/'

    # override
    def getPath(self, parent):
        '''
        @param: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        self._path = QFileDialog.getExistingDirectory(parent, _('Choose file...'), self.standardPath())
        return self._path

    # override
    def prepareImport(self):
        '''
        @brief: Prepare import (check if file exists, ...)
        @return: bool
        '''
        if not pathexists(self._path):
            self._setError(_('Directory does not exists.'))
            return False

        return True

    # override
    def importBookmarks(self):
        '''
        @brief: Import bookmarks (it must return root folder)
        '''
        root = BookmarkItem(BookmarkItem.Folder)
        root.setTitle('Internet Explorer Import')

        self._readDir(QDir(self._path), root)
        return root

    def _readDir(self, dir_, parent):
        '''
        @param: dir_ QDir
        @param: parent BookmarkItem
        '''
        for file_ in dir_.entryInfoList(QDir.Dirs | QDir.Files | QDir.NoDotAndDotDot):
            # file_ QFileInfo
            if file_.isDir():
                folder = BookmarkItem(BookmarkItem.Folder, parent)
                folder.setTitle(file_.baseName())

                folderDir = QDir(dir_)
                folderDir.cd(file_.baseName())
                self._readDir(folderDir, folder)
            elif file_.isFile():
                urlFile = QSettings(file_.absoluteFilePath(), QSettings.IniFormat)
                url = urlFile.value('InternetShortcut/URL', type=QUrl)

                item = BookmarkItem(BookmarkItem.Url, parent)
                item.setTitle(file_.baseName())
                item.setUrl(url)
