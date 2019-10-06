from os import makedirs, remove
from json import dumps as jdumps
from os.path import exists as pathexists
from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QUrl
from PyQt5.Qt import QCryptographicHash
from PyQt5.Qt import QDir
from PyQt5.Qt import QPixmap
from PyQt5.Qt import pyqtSlot
from mc.tools.AutoSaver import AutoSaver
from mc.app.Settings import Settings
from mc.app.DataPaths import DataPaths
from mc.common.globalvars import gVar
from mc.tools.PageThumbnailer import PageThumbnailer

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
        self._maxPagesInRow = 4
        self._sizeOfSpeedDials = 231
        self._sdcentered = 0

        self._pages = []  # QList<Page>
        self._autoSaver = AutoSaver(self)  # AutoSaver

        self._loaded = False
        self._regenerateScript = True

        self._autoSaver.save.connect(self._saveSettings)
        self.pagesChanged.connect(self._autoSaver.changeOccurred)

    def loadSettings(self):
        self._loaded = True

        settings = Settings()
        settings.beginGroup('SpeedDial')
        allPages = settings.value('pages', '')
        self.setBackgroundImage(settings.value('background', ''))
        self._backgroundImageSize = settings.value('backsize', 'auto')
        self._maxPagesInRow = settings.value('pagesrow', 4)
        self._sizeOfSpeedDials = settings.value('sdsize', 231)
        self._sdcentered = settings.value('sdcenter', False)
        settings.endGroup()

        self.changed(allPages)

        self._thumbnailsDir = DataPaths.currentProfilePath() + '/thumbnails/'

        # If needed, create thumbnails directory
        if not pathexists(self._thumbnailsDir):
            makedirs(self._thumbnailsDir)

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
        if not self._loaded:
            self.loadSettings()

        if key < 0 or len(self._pages) <= key:
            return QUrl()

        return QUrl.fromEncoded(self._pages[key].url.encode())

    def addPage(self, url, title):
        '''
        @param: url QUrl
        @param: title QString
        '''
        if not self._loaded:
            self.loadSettings()

        if url.isEmpty():
            return

        page = self.Page()
        page.title = self._escapeTitle(title)
        page.url = self._escapeUrl(url.toString())

        self._pages.append(page)
        self._regenerateScript = True

        self.pagesChanged.emit()

    def removePage(self, page):
        '''
        @param: page Page
        '''
        if not self._loaded:
            self.loadSettings()

        self.removeImageForUrl(page.url)
        self._pages.remove(page)
        self._regenerateScript = True

        self.pagesChanged.emit()

    def pagesInRow(self):
        '''
        @return: int
        '''
        if not self._loaded:
            self.loadSettings()

        return self._maxPagesInRow

    def sdSize(self):
        '''
        @return: int
        '''
        if not self._loaded:
            self.loadSettings()

        return self._sizeOfSpeedDials

    def sdCenter(self):
        '''
        @return: bool
        '''
        if not self._loaded:
            self.loadSettings()

        return self._sdcentered

    def backgroundImage(self):
        '''
        @return: QString
        '''
        if not self._loaded:
            self.loadSettings()

        return self._backgroundImage

    def backgroundImageUrl(self):
        '''
        @return: QString
        '''
        if not self._loaded:
            self.loadSettings()

        return self._backgroundImageUrl

    def backgroundImageSize(self):
        '''
        @return: QString
        '''
        if not self._loaded:
            self.loadSettings()

        return self._backgroundImageSize

    def initialScript(self):
        '''
        @return: QString
        '''
        if not self._loaded:
            self.loadSettings()

        if not self._regenerateScript:
            return self._initialScript

        self._regenerateScript = False
        self._initialScript = ''

        pages = []

        for page in self._pages:
            imgSource = self._genFileNameByUrl(page.url)

            if not pathexists(imgSource):
                imgSource = 'qrc:html/loading.gif'

                if not page.isValid():
                    imgSource = ''
            else:
                imgSource = gVar.appTools.pixmapToDataUrl(QPixmap(imgSource)).toString()

            map_ = {}
            map_['url'] = page.url
            map_['title'] = page.title
            map_['img'] = imgSource
            pages.append(map_)

        self._initialScript = jdumps(pages)
        return self._initialScript

    def pages(self):
        '''
        @return: QList<Page>
        '''
        if not self._loaded:
            self.loadSettings()

        return self._pages

    # Q_SIGNALS
    pagesChanged = pyqtSignal()
    thumbnailLoaded = pyqtSignal(str, str)  # url, src
    pageTitleLoaded = pyqtSignal(str, str)  # url, title

    # public Q_SLOTS:
    @pyqtSlot(str)
    def changed(self, allPages):
        '''
        @param: allPages QString
        '''
        entries = [ item.strip() for item in allPages.split('";') ]
        entries = [ item for item in entries if item ]
        self._pages.clear()

        for entry in entries:
            if not entry:
                continue

            tmp = [ item.strip() for item in entry.split('"|') ]
            tmp = [ item for item in tmp if item ]
            if len(tmp) != 2:
                continue

            page = self.Page()
            page.url = tmp[0][5:].strip().rstrip('/\\')
            page.title = tmp[1][7:].strip()

            self._pages.append(page)

        self._regenerateScript = True
        self.pagesChanged.emit()

    @pyqtSlot(str, bool)
    def loadThumbnail(self, url, loadTitle):
        '''
        @param: url QString
        @param: loadTitle bool
        '''
        thumbnailer = PageThumbnailer(self)
        thumbnailer.setUrl(QUrl.fromEncoded(url.encode()))
        thumbnailer.setLoadTitle(loadTitle)
        thumbnailer.thumbnailCreated.connect(self._thumbnailCreated)

        thumbnailer.start()

    def _genFileNameByUrl(self, url):
        '''
        @param: url QString
        '''
        # QByteArray
        hexBytes = QCryptographicHash.hash(url.encode(),
            QCryptographicHash.Md4).toHex()
        return self._thumbnailsDir + hexBytes.data().decode() + '.png'

    @pyqtSlot(str)
    def removeImageForUrl(self, url):
        '''
        @param: url QString
        '''
        fileName = self._genFileNameByUrl(url)

        if pathexists(fileName):
            remove(fileName)

    @pyqtSlot(result=list)
    def getOpenFileName(self):
        '''
        @return: QStringList
        '''
        fileTypes = '%s(*.png *.jpg *.jpeg *.bmp *gif *.svg *.tiff)' % _('Image files')
        image = gVar.appTools.getOpenFileName('SpeedDial-GetOpenFileName', None,
                _('Click to select image...'), QDir.homePath(), fileTypes)

        if not image:
            return []

        return [ gVar.appTools.pixmapToDataUrl(QPixmap(image)).toString(),
            QUrl.fromLocalFile(image).toEncoded() ]

    @pyqtSlot(str, result=str)
    def urlFromUserInput(self, url):
        '''
        @param: QString
        '''
        return QUrl.fromUserInput(url).toString()

    @pyqtSlot(str)
    def setBackgroundImage(self, image):
        '''
        @param: image QString
        '''
        self._backgroundImage = gVar.appTools.pixmapToDataUrl(
            QPixmap(QUrl(image).toLocalFile())
        ).toString()

    @pyqtSlot(str)
    def setBackgourndImageSize(self, size):
        '''
        @param: size QString
        '''
        self._backgroundImageSize = size

    @pyqtSlot(int)
    def setPageInRow(self, count):
        '''
        @param: count int
        '''
        self._maxPagesInRow = count

    @pyqtSlot(int)
    def setSdSize(self, count):
        '''
        @param: count int
        '''
        self._sizeOfSpeedDials = count

    @pyqtSlot(bool)
    def setSdCentered(self, centered):
        '''
        @param: centered bool
        '''
        self._sdcentered = centered
        self._autoSaver.changeOccurred()

    # private Q_SLOTS:
    def _thumbnailCreated(self, pixmap):
        '''
        @param: pixmap QPixmap
        '''
        thumbnailer = self.sender()
        if not isinstance(thumbnailer, PageThumbnailer):
            return

        loadTitle = thumbnailer.loadTitle()
        title = thumbnailer.title()
        url = thumbnailer.url().toString()
        fileName = self._genFileNameByUrl(url)

        if pixmap.isNull():
            fileName = ':/html/broken-page.svg'
            title = _('Unable to load')
        else:
            if not pixmap.save(fileName, 'PNG'):
                print('WARNING: SpeedDial::thumbnailCreated cannot save thumbnail to %s' % fileName)

        self._regenerateScript = True
        thumbnailer.deleteLater()

        if loadTitle:
            self.pageTitleLoaded.emit(url, title)

        imgUrl = gVar.appTools.pixmapToDataUrl(QPixmap(fileName)).toString()
        self.thumbnailLoaded.emit(url, imgUrl)

    def _saveSettings(self):
        if not self._loaded:
            self.loadSettings()

        settings = Settings()
        settings.beginGroup('SpeedDial')
        settings.setValue('pages', self._generateAllPages())
        settings.setValue('background', self._backgroundImageUrl)
        settings.setValue('backsize', self._backgroundImageSize)
        settings.setValue('pagesrow', self._maxPagesInRow)
        settings.setValue('sdsize', self._sizeOfSpeedDials)
        settings.setValue('sdcenter', self._sdcentered)
        settings.endGroup()

    # private:
    def _escapeTitle(self, title):
        '''
        @return: QString
        '''
        title = title.replace('"', '&quot;') \
            .replace("'", '&apos;')
        return title

    def _escapeUrl(self, url):
        '''
        @param: url QString
        @return: QString
        '''
        url = url.replace('"', '') \
            .replace("'", '')
        return url

    def _generateAllPages(self):
        '''
        @return: QString
        '''
        allPages = ''

        for page in self._pages:
            string = 'url:"%s"|title:"%s";' % (page.url, page.title)
            allPages += string

        return allPages
