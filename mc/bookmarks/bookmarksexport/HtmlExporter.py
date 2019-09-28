from .BookmarksExporter import BookmarksExporter
from PyQt5.Qt import QDir
from mc.common.globalvars import gVar
from ..BookmarkItem import BookmarkItem

class HtmlExporter(BookmarksExporter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ''

    # override
    def name(self):
        '''
        @return: QString
        '''
        return _('HTML File') + ' (bookmarks.html)'

    def getPath(self, parent):
        '''
        @param: parent QWidget
        @return: QString
        '''
        defaultPath = QDir.homePath() + '/bookmarks.html'
        filter_ = _('HTML Bookmarks') + '.html'
        self._path = gVar.appTools.getSaveFileName('HtmlExporter', parent,
                _('Choose file...'), defaultPath, filter_)
        return self._path

    def exportBookmarks(self, root):
        '''
        @param: root BookmarkItem
        @return: bool
        '''
        try:
            with open(self._path) as fp:
                fp.writelines(
                    [
                        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
                        "<!-- This is an automatically generated file.",
                        "     It will be read and overwritten.",
                        "     DO NOT EDIT! -->",
                        "<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">",
                        "<TITLE>Bookmarks</TITLE>",
                        "<H1>Bookmarks</H1>"
                    ]
                )
                self._writeBookmark(root, fp, 0)
            return True
        except IOError:
            self._setError(_('Cannot open file for writing!'))
            return False

    # private:
    def _writeBookmark(self, item, fp, level):
        '''
        @param: item BookmarkItem
        @param: stream QTextStream
        @param: level int
        '''
        assert(item)

        indent = ' ' * level * 4

        itemType = item.type()
        if itemType == BookmarkItem.Url:
            fp.write('%s<DT><A HREF="%s">%s</A>\n' % (indent,
                item.urlString(), item.title()
            ))
        elif itemType == BookmarkItem.Separator:
            fp.write('%s<HR>\n' % indent)
        elif itemType == BookmarkItem.Folder:
            fp.write('%s<DT><H3>%s</H3>\n' % (indent, item.title()))
            fp.write('%s<DL><p>\n')
            for child in item.children():
                self._writeBookmark(child, fp, level + 1)
            fp.write('%s</p></DL>\n')
        elif itemType == BookmarkItem.Root:
            fp.write('%s<DL><p>\n')
            for child in item.children():
                self._writeBookmark(child, fp, level + 1)
            fp.write('%s</p></DL>\n')
