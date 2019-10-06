from PyQt5.Qt import QObject
from PyQt5.Qt import QUrl
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QSize
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.Qt import Qt
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QTimer
from mc.common.globalvars import gVar
from mc.webengine.WebView import WebView
from mc.tools.Scripts import Scripts

class PageThumbnailer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._view = QQuickWidget()  # QQuickWidget
        self._size = QSize(450, 253) * gVar.app.devicePixelRatio()
        self._url = QUrl()
        self._title = ''
        self._loadTitle = False

        self._view.setAttribute(Qt.WA_DontShowOnScreen)
        self._view.setSource(QUrl('qrc:data/thumbnailer.qml'))
        self._view.rootContext().setContextProperty('thumbnailer', self)
        self._view.show()

    def setSize(self, size):
        if size.isValid():
            self._size = size

    def setUrl(self, url):
        if url.isValid():
            self._url = url

    def url(self):
        return self._url

    def loadTitle(self):
        '''
        @return: bool
        '''
        return self._loadTitle

    def setLoadTitle(self, load):
        '''
        @param: load bool
        '''
        self._loadTitle = load

    def title(self):
        title = self._title
        if not title:
            title = self._url.host()
        if not title:
            title = self._url.toString()
        return title

    def start(self):
        if self._view.rootObject() and WebView.isUrlValid(self._url):
            self._view.rootObject().setProperty('url', self._url)
        else:
            def func():
                self.thumbnailCreated.emit(QPixmap())
            QTimer.singleShot(500, func)

    # Q_SIGNALS:
    thumbnailCreated = pyqtSignal(QPixmap)

    # public Q_SLOTS:
    def afterLoadScript(self):
        '''
        @return: QString
        '''
        return Scripts.setCss('::~webkit-scrollbar{display:none;}')

    def createThumbnail(self, status):
        '''
        @param: status bool
        '''
        if not status:
            self.thumbnailCreated.emit(QPixmap())
            return

        def func():
            self._title = self._view.rootObject().property('title').strip()
            img = self._view.grabFramebuffer().scaled(self._size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(img)
            self.thumbnailCreated.emit(pixmap)
        QTimer.singleShot(1000, func)
