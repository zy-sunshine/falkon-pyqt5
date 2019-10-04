from PyQt5.Qt import QUrl, QIcon, QTime
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QStyle

class BookmarkItem(object):
    # enum Type
    Root = 0
    Url = 1
    Folder = 2
    Separator = 3
    Invalid = 4
    TYPE_STR_CHOICES = (
        (Url, 'url'),
        (Folder, 'folder'),
        (Separator, 'separator'),
    )

    def __init__(self, type_, parent=None):
        self._type = type_
        self._parent = None  # BookmarkItem
        self._children = []  # QList<BookmarkItem>

        self._url = QUrl()
        self._title = ''
        self._description = ''
        self._keyword = ''
        self._icon = QIcon()
        self._iconTime = QTime()
        self._visitCount = 0
        self._expanded = False
        self._sidebarExpanded = False

        if parent:
            parent.addChild(self)
        assert(self._parent == parent)

    def type(self):
        return self._type

    def setType(self, type_):
        self._type = type_

    def isFolder(self):
        return self._type == self.Folder

    def isUrl(self):
        return self._type == self.Url

    def isSeparator(self):
        return self._type == self.Separator

    def parent(self):
        '''
        @return: BookmarkItem
        '''
        return self._parent

    def children(self):
        '''
        @return: QList<BookmarkItem>
        '''
        return self._children

    def icon(self):
        '''
        @return: QIcon
        '''
        # Cache icon for 20 seconds
        iconCacheTime = 20 * 1000

        if self._type == self.Url:
            if self._iconTime.isNull() or self._iconTime.elapsed() > iconCacheTime:
                self._icon = IconProvider.iconForUrl(self._url)
                self._iconTime.restart()
            return self._icon
        elif self._type == self.Folder:
            return IconProvider.standardIcon(QStyle.SP_DirIcon)
        else:
            return QIcon()

    def setIcon(self, icon):
        self._icon = icon

    def urlString(self):
        return self._url.toEncoded().data().decode()

    def url(self):
        '''
        @return: QUrl
        '''
        return self._url

    def setUrl(self, url):
        '''
        @param: url QUrl
        '''
        self._url = url

    def title(self):
        '''
        @return: QString
        '''
        return self._title

    def setTitle(self, title):
        '''
        @param: title QString
        '''
        self._title = title

    def description(self):
        return self._description

    def setDescription(self, description):
        self._description = description

    def keyword(self):
        return self._keyword

    def setKeyword(self, keyword):
        self._keyword = keyword

    def visitCount(self):
        '''
        @return: int
        '''
        return self._visitCount

    def setVisitCount(self, count):
        self._visitCount = count

    def updateVisitCount(self):
        '''
        @brief: Increments visitCount() (may also update last load time when implemented)
        '''
        self._visitCount += 1

    def isExpanded(self):
        if self._type == self.Root:
            return True
        return self._expanded

    def setExpanded(self, expanded):
        self._expanded = expanded

    def isSidebarExpanded(self):
        '''
        @brief: Expanded state in Sidebar
        '''
        if self._type == self.Root:
            return True
        else:
            return self._sidebarExpanded

    def setSidebarExpanded(self, expanded):
        self._sidebarExpanded = expanded

    def addChild(self, child, index=-1):
        '''
        @param: child BookmarkItem
        '''
        if child._parent:
            child._parent.removeChild(child)

        child._parent = self
        if index < 0:
            self._children.append(child)
        else:
            self._children.insert(index, child)

    def removeChild(self, child):
        '''
        @param: child BookmarkItem
        '''
        child._parent = None
        self._children.remove(child)

    @classmethod
    def typeFromString(cls, string):
        '''
        @param: string QString
        @return: Type(enum int)
        '''
        for type_, str_ in cls.TYPE_STR_CHOICES:
            if string == str_:
                return type_
        else:
            return cls.Invalid

    @classmethod
    def typeToString(cls, type_):
        '''
        @parma: type_ Type(enum int)
        @return: QString
        '''
        for type0, str_ in cls.TYPE_STR_CHOICES:
            if type0 == type_:
                return str_
        else:
            return 'invalid'
