from PyQt5.Qt import QObject

class BookmarksExporter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._error = ''

    def error(self):
        return bool(self._error)

    def errorString(self):
        return self._error

    def name(self):
        '''
        @return: QString
        '''
        raise NotImplementedError

    def getPath(self, parent):
        '''
        @brief: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        raise NotImplementedError

    def exportBookmarks(self, root):
        '''
        @param: root BookmarkItem
        @return: bool
        '''
        raise NotImplementedError

    # protected:
    def _setError(self, error):
        '''
        @brief: Empty error = no error
        @param: error QString
        '''
        self._error = error
