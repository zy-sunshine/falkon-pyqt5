from PyQt5.Qt import QImage
from PyQt5.Qt import QIcon
from threading import Lock

# Need to be QWidget subclass, otherwise qproperty- setting won't work
# but in Python could inherate form object directly
class IconProvider(object):
    def __init__(self):
        self._emptyWebImage = QImage()
        self._bookmarkIcon = QIcon()
        self._iconBuffer = []  # QVector<[QUrl, QImage]>
        # TODO: cache limit size
        self._urlImageCache = {}  # QCache<QByteArray, QImage>
        self._iconCacheMutex = Lock()  # QMutex

        self._autoSaver = None  # AUtoSaver

    def saveIcon(self, view):
        '''
        @param: view WebView
        '''
        pass

    def bookmarkIcon(self):
        '''
        @return: QIcon
        '''
        return QIcon()

    def setBookmarkIcon(self, icon):
        '''
        @param: icon QIcon
        '''
        pass

    bookmarkIcon = property(bookmarkIcon, setBookmarkIcon)

    # QStyle equivalent
    @classmethod
    def standardIcon(cls, icon):
        '''
        @param: icon QStyle::StandardPixmap
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def newTabIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def newWindowIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def privateBrowsingIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def settingsIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon()

    # Icon for empty page
    @classmethod
    def emptyWebIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def emptyWebImage(cls):
        '''
        @return: QIcon
        '''
        return QIcon()

    # Icon for url (only available for urls in history)
    @classmethod
    def iconForUrl(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def imageForUrl(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        return QIcon()

    # Icon for domain (only available for urls in history)
    @classmethod
    def iconForDomain(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def imageForDomain(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        return QIcon()

    @classmethod
    def instance(cls):
        '''
        @return: IconProvider
        '''
        return QIcon()

    # public Q_SLOTS:
    def saveIconsToDatabase(self):
        pass

    def clearOldIconsInDatabase(self):
        pass

    # private:
    def _iconFromImage(self, image):
        '''
        @param: image QImage
        @return: QIcon
        '''
        return QIcon()
