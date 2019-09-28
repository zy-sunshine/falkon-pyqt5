from PyQt5.Qt import QObject

class BookmarksImporter(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self._error = ''

    def error(self):
        '''
        @return: bool
        '''
        return bool(self._error)

    def errorString(self):
        '''
        @return: QString
        '''
        return self._error

    def description(self):
        '''
        @return: QString
        '''
        raise NotImplementedError

    def standardPath(self):
        '''
        @return: QString
        '''
        raise NotImplementedError

    def getPath(self, parent):
        '''
        @param: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        raise NotImplementedError

    def prepareImport(self):
        '''
        @brief: Prepare import (check if file exists, ...)
        @return: bool
        '''
        raise NotImplementedError

    def importBookmarks(self):
        '''
        @brief: Import bookmarks (it must return root folder)
        '''
        raise NotImplementedError

    # protected:
    def _setError(self, error):
        '''
        @brief: Empty error = no error
        @param: error QString
        '''
        self._error = error
