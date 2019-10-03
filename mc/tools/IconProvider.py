from PyQt5.Qt import QImage
from PyQt5.Qt import QIcon
from threading import Lock
from mc.common.designutil import Singleton
from PyQt5.Qt import QStyle
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import Qt
from PyQt5.Qt import QUrl
from PyQt5.Qt import QBuffer
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QPixmap
from PyQt5.QtWidgets import QWidget
from .AutoSaver import AutoSaver
from mc.common.globalvars import gVar
from mc.common.models import IconsDbModel
from mc.common.models import HistoryDbModel

def encodeUrl(url):
    '''
    @param: url QUrl
    '''
    return url.toEncoded(QUrl.RemoveFragment | QUrl.StripTrailingSlash)

# Need to be QWidget subclass, otherwise qproperty- setting won't work
# but in Python could inherate form object directly
class IconProvider(QWidget):
    _instance = None
    def __init__(self):
        super().__init__()
        self._emptyWebImage = QImage()
        self._bookmarkIcon = QIcon()
        self._iconBuffer = []  # QVector<[QUrl, QImage]>
        # TODO: cache limit size
        self._urlImageCache = {}  # QCache<QByteArray, QImage>
        self._iconCacheMutex = Lock()  # QMutex

        self._autoSaver = AutoSaver(self)  # AutoSaver
        self._autoSaver.save.connect(self.saveIconsToDatabase)

    def saveIcon(self, view):
        '''
        @param: view WebView
        '''
        # Don't save icons in private mode
        if gVar.app.isPrivate():
            return

        icon = view.icon(True)
        if icon.isNull():
            return

        ignoredSchemes = [
            'app', 'ftp', 'file', 'view-source', 'data', 'about'
        ]

        if view.url().scheme() in ignoredSchemes:
            return

        for idx in range(len(self._iconBuffer)):
            if self._iconBuffer[idx][0] == view.url():
                self._iconBuffer.pop(idx)
                break

        item = (view.url(), icon.pixmap(16).toImage())

        self._autoSaver.changeOccurred()
        self._iconBuffer.append(item)

    def bookmarkIcon(self):
        '''
        @return: QIcon
        '''
        return QIcon.fromTheme('bookmarks', self._bookmarkIcon)

    def setBookmarkIcon(self, icon):
        '''
        @param: icon QIcon
        '''
        self._bookmarkIcon = icon

    bookmarkIcon = property(bookmarkIcon, setBookmarkIcon)

    # QStyle equivalent
    @classmethod  # noqa C901
    def standardIcon(cls, icon):
        '''
        @param: icon QStyle::StandardPixmap
        @return: QIcon
        '''
        defIcon = QApplication.style().standardIcon(icon)
        if icon == QStyle.SP_MessageBoxCritical:
            return QIcon.fromTheme('dialog-error', defIcon)
        elif icon == QStyle.SP_MessageBoxInformation:
            return QIcon.fromTheme('dialog-information', defIcon)
        elif icon == QStyle.SP_MessageBoxQuestion:
            return QIcon.fromTheme('dialog-question', defIcon)
        elif icon == QStyle.SP_MessageBoxWarning:
            return QIcon.fromTheme('dialog-warning', defIcon)
        elif icon == QStyle.SP_DialogCloseButton:
            return QIcon.fromTheme('dialog-close', defIcon)
        elif icon == QStyle.SP_BrowserStop:
            return QIcon.fromTheme('progress-stop', defIcon)
        elif icon == QStyle.SP_BrowserReload:
            return QIcon.fromTheme('view-refresh', defIcon)
        elif icon == QStyle.SP_FileDialogToParent:
            return QIcon.fromTheme('go-up', defIcon)
        elif icon == QStyle.SP_ArrowUp:
            return QIcon.fromTheme('go-up', defIcon)
        elif icon == QStyle.SP_ArrowDown:
            return QIcon.fromTheme('go-down', defIcon)
        elif icon == QStyle.SP_ArrowForward:
            if QApplication.layoutDirection() == Qt.RightToLeft:
                return QIcon.fromTheme('go-previous', defIcon)
            else:
                return QIcon.fromTheme('go-next', defIcon)
        elif icon == QStyle.SP_ArrowBack:
            if QApplication.layoutDirection() == Qt.RightToLeft:
                return QIcon.fromTheme('go-next', defIcon)
            else:
                return QIcon.fromTheme('go-previous', defIcon)
        else:
            return defIcon

    @classmethod
    def newTabIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon.fromTheme('tab-new', QIcon(':/icons/menu/tab-new.svg'))

    @classmethod
    def newWindowIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon.fromTheme('window-new', QIcon(':/icons/menu/window-new.svg'))

    @classmethod
    def privateBrowsingIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon.fromTheme('view-private-symbolic', QIcon(':/icons/menu/privatebrowsing.png'))

    @classmethod
    def settingsIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon.fromTheme('configure', QIcon(':/icons/menu/settings.svg'))

    # Icon for empty page
    @classmethod
    def emptyWebIcon(cls):
        '''
        @return: QIcon
        '''
        return QIcon(QPixmap.fromImage(cls.emptyWebImage()))

    @classmethod
    def emptyWebImage(cls):
        '''
        @return: QIcon
        '''
        if cls.instance()._emptyWebImage.isNull():
            cls.instance()._emptyWebImage = QIcon(':/icons/other/webpage.svg').pixmap(16).toImage()

        return cls.instance()._emptyWebImage

    # Icon for url (only available for urls in history)
    @classmethod
    def iconForUrl(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        return cls.instance()._iconFromImage(cls.imageForUrl(url, allowNull))

    @classmethod
    def imageForUrl(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QImage
        '''
        if not url.path():
            return allowNull and QImage() or cls.emptyWebImage()

        with cls.instance()._iconCacheMutex:
            encUrl = encodeUrl(url)

            # find in urlImageCache
            img = cls.instance()._urlImageCache.get(encUrl, None)
            if img:
                if not img.isNull():
                    return img
                if not allowNull:
                    return cls.emptyWebImage()
                return img

            # find from icon buffer
            for url0, img in cls.instance()._iconBuffer:
                if encodeUrl(url0) == encUrl:
                    return img

            escapedUrl = gVar.appTools.escapeSqlGlobString(encUrl.data().decode())
            urlPattern = '%s*' % escapedUrl
            icon = IconsDbModel.select().filter(IconsDbModel.url.regexp(urlPattern)).first()
            img = QImage()
            if icon:
                img.loadFromData(icon.icon)
            cls.instance()._urlImageCache[encUrl] = img

            if not img.isNull():
                return img
            if not allowNull:
                return cls.emptyWebImage()
            return img

    # Icon for domain (only available for urls in history)
    @classmethod
    def iconForDomain(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        return cls.instance()._iconFromImage(cls.imageForDomain(url, allowNull))

    @classmethod
    def imageForDomain(cls, url, allowNull=False):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        if not url.host():
            if allowNull:
                return QImage()
            return cls.emptyWebImage()

        with cls.instance()._iconCacheMutex:
            for url0, img in cls.instance()._iconBuffer:
                if url0.host() == url.host():
                    return img

            escapedHost = gVar.appTools.escapeSqlGlobString(url.host())
            hostPattern = '*%s*' % escapedHost
            icon = IconsDbModel.select().filter(IconsDbModel.url.regexp(hostPattern)).first()
            img = QImage()
            if icon:
                img.loadFromData(icon.icon)

            if not img.isNull():
                return img
            if not allowNull:
                return cls.emptyWebImage()
            return img

    # public Q_SLOTS:
    def saveIconsToDatabase(self):
        gVar.executor.submit(self._saveIconsToDatabase)

    def _saveIconsToDatabase(self):
        with self._iconCacheMutex:
            for url, img in self._iconBuffer:
                ba = QByteArray()
                buff = QBuffer(ba)
                buff.open(QIODevice.WriteOnly)
                img.save(buff, 'PNG')

                # QByteArray
                encodedUrl = encodeUrl(url)
                self._urlImageCache.pop(encodedUrl, None)

                IconsDbModel.insert(icon=buff.data(),
                        url=encodedUrl.data().decode()) \
                    .on_conflict('replace') \
                    .execute()
            self._iconBuffer.clear()

    def clearOldIconsInDatabase(self):
        # Delete icons for entries older than 6 months
        gVar.executor.submit(self._clearOldIconsInDatabase)

    def _clearOldIconsInDatabase(self):
        date = QDateTime.currentDateTime().addMonths(-6)

        urls = HistoryDbModel.select().where(HistoryDbModel.date < date.toMSecsSinceEpoch())
        IconsDbModel.delete().where(IconsDbModel.url.in_(urls))

    # private:
    def _iconFromImage(self, image):
        '''
        @param: image QImage
        @return: QIcon
        '''
        return QIcon(QPixmap.fromImage(image))

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
