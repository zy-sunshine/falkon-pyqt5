from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from mc.tools.AutoSaver import AutoSaver

class SpeedDial(QObject):
    class Page:
        def __init__(self):
            self.title = ''
            self.url = ''

        def isValid(self):
            return bool(self.url)

        def __eq__(self, other):
            return self.title == other.title and \
                self.url == other.url

    def __init__(self, parent=None):
        '''
        @param: parent QObject
        '''
        super().__init__(parent)
        self._initialScript = ''
        self._thumbnailsDir = ''
        self._backgroundImage = ''
        self._backgroundImageUrl = ''
        self._backgroundImageSize = ''
        self._maxPageInRow = 4
        self._sizeOfSpeedDials = 231
        self._sdcentered = 0

        self._pages = []  # QList<Page>
        self._autoSaver = AutoSaver(self)  # AutoSaver

        self._loaded = False
        self._regenerateScript = True

        self._autoSaver.save.connect(self._saveSettings)
        self.pagesChanged.connect(self._autoSaver.changeOccurred)

    def loadSettings(self):
        pass

    def pageForUrl(self, url):
        '''
        @param: url QUrl
        @return: Page
        '''
        urlString = url.toString().rstrip('/\\')
        for page in self._pages:
            if page.url == urlString:
                return page
        return self.Page()

    def urlForShortcut(self, key):
        '''
        @param: key int
        @return: QUrl
        '''
        pass

    def addPage(self, url, title):
        '''
        @param: url QUrl
        @param: title QString
        '''
        pass

    def removePage(self, page):
        '''
        @param: page Page
        '''
        pass

    def pagesInRow(self):
        '''
        @return: int
        '''
        pass

    def sdSize(self):
        '''
        @return: int
        '''
        pass

    def sdCenter(self):
        '''
        @return: bool
        '''
        pass

    def backgroundImage(self):
        '''
        @return: QString
        '''
        pass

    def backgroundImageUrl(self):
        '''
        @return: QString
        '''
        pass

    def backgroundImageSize(self):
        '''
        @return: QString
        '''
        pass

    def initialScript(self):
        '''
        @return: QString
        '''
        pass

    def pages(self):
        '''
        @return: QList<Page>
        '''
        pass

    # Q_SIGNALS
    pagesChanged = pyqtSignal()
    thumbnailLoaded = pyqtSignal(str, str)  # url, src
    pageTitleLoaded = pyqtSignal(str, str)  # url, title

    # public Q_SLOTS:
    def changed(self, allPages):
        '''
        @param: allPages QString
        '''
        pass

    def loadThumbnail(self, url, loadTitle):
        '''
        @param: url QString
        @param: loadTitle bool
        '''
        pass

    def removeImageForUrl(self, url):
        '''
        @param: url QString
        '''
        pass

    def getOpenFileName(self):
        '''
        @return: QStringList
        '''
        pass

    def urlFromUserInput(self, url):
        '''
        @param: QString
        '''
        pass

    def setBackgroundImage(self, image):
        '''
        @param: image QString
        '''
        pass

    def setBackgourndImageSize(self, size):
        '''
        @param: size QString
        '''
        pass

    def setPageInRow(self, count):
        '''
        @param: count int
        '''
        pass

    def setSdSize(self, size):
        '''
        @param: size int
        '''
        pass

    def setSdCentered(self, centered):
        '''
        @param: centered bool
        '''
        pass

    # private Q_SLOTS:
    def _thumbnailCreated(self, pixmap):
        '''
        @param: pixmap QPixmap
        '''
        pass

    def _saveSettings(self):
        pass

    # private:
    def _escapeTitle(self, string):
        '''
        @return: QString
        '''
        pass

    def _escapeUrl(self, url):
        '''
        @param: url QString
        @return: QString
        '''
        pass

    def _generateAllPages(self):
        '''
        @return: QString
        '''
        pass
