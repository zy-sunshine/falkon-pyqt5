import re
from .BookmarksImporter import BookmarksImporter
from PyQt5.QtWidgets import QFileDialog
from PyQt5.Qt import QDir
from mc.bookmarks.BookmarkItem import BookmarkItem
from PyQt5.Qt import QUrl

def _min(a, b):
    if a > -1 and b > -1:
        return min(a, b)
    if a > -1:
        return a
    else:
        return b

class HtmlImporter(BookmarksImporter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ''
        self._content = ''

    # override
    def description(self):
        '''
        @return: QString
        '''
        return _("You can import bookmarks from any browser that supports HTML exporting. "
            "This file has usually these suffixes")

    # override
    def standardPath(self):
        '''
        @return: QString
        '''
        return '.htm, .html'

    # override
    def getPath(self, parent):
        '''
        @param: Get filename from user (or a directory)
        @param: parent QWidget
        @return: QString
        '''
        filter_ = _('HTML Bookmarks') + '(*.htm *.html)'
        self._path = QFileDialog.getOpenFileName(parent, _('Choose file...'), QDir.homePath(), filter_)
        return self._path

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
        c = self._content
        c = c.replace("<DL", "<dl")
        c = c.replace("</DL", "</dl")
        c = c.replace("<DT", "<dt")
        c = c.replace("</DT", "</dt")
        c = c.replace("<P", "<p")
        c = c.replace("</P", "</p")
        c = c.replace("<A", "<a")
        c = c.replace("</A", "</a")
        c = c.replace("HREF=", "href=")
        c = c.replace("<H3", "<h3")
        c = c.replace("</H3", "</h3")

        c = c[:c.rfind('</dl><p>')]
        start = c.find("<dl><p>")

        root = BookmarkItem(BookmarkItem.Folder)
        root.setTitle("HTML Import")

        folders = []  # QList<BookmarkItem*>
        folders.append(root)

        while start > 0:
            string = bookmarks[start:]

            posOfFolder = string.find("<dt><h3")
            posOfEndFolder = string.find("</dl><p>")
            posOfLink = string.find("<dt><a")

            nearest = _min(posOfLink, _min(posOfFolder, posOfEndFolder))
            if nearest == -1:
                break

            if nearest == posOfFolder:
                # Next is folder
                rx = re.compile(r"<dt><h3(.*)>(.*)</h3>")
                match = rx.search(string)
                folderName = match.group(2).strip()

                folder = BookmarkItem(BookmarkItem.Folder, not folders and root or folders[-1])
                folder.setTitle(folderName)
                folders.append(folder)

                start += posOfFolder + len(match.group(0))
            elif nearest == posOfEndFolder:
                # Next is end of folder
                if folders:
                    folders.pop(-1)

                start += posOfEndFolder + 8
            else:
                # Next is link
                rx = re.compile(r"<dt><a(.*)>(.*)</a>")
                match = rx.search(string)

                arguments = match.group(1)
                linkName = match.group(2).strip()

                rx2 = re.compile(r"href=\"(.*)\"")
                match2 = rx2.search(arguments)

                url = QUrl.fromEncoded(match2.group(1).strip())

                start += posOfLink + len(match.group(0))

                if not url or url.scheme() == "place" or url.scheme() == "about":
                    continue

                b = BookmarkItem(BookmarkItem.Url, not folders and root or folders[-1])
                b.setTitle(not linkName and url.toString() or linkName)
                b.setUrl(url)

        return root
