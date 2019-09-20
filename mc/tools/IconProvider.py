from PyQt5.Qt import QImage
from PyQt5.Qt import QIcon
from threading import Lock
from mc.common.designutil import Singleton
from PyQt5.Qt import QStyle
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import Qt

# Need to be QWidget subclass, otherwise qproperty- setting won't work
# but in Python could inherate form object directly
class IconProvider(Singleton):
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
