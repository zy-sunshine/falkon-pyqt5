from os.path import isfile, isdir, dirname, basename, abspath
from os.path import join as pathjoin, exists as pathexists
from PyQt5.Qt import QFileDialog
from PyQt5.Qt import QKeySequence
from mc.app.Settings import Settings
from mc.common.designutil import Singleton
from PyQt5.Qt import QPalette
from PyQt5.Qt import QStylePainter
from PyQt5.QtWidgets import QApplication
from PyQt5.Qt import QFile
from PyQt5.Qt import QUrl
from PyQt5.Qt import QFileInfo

class AppTools(Singleton):

    def pixmapToByteArray(self, pix):
        '''
        @param: pix QPixmap
        @return: QByteArray
        '''
        pass

    def pixmapFromByteArray(self, data):
        '''
        @param: data QByteArray
        @return: QPixmap
        '''
        pass

    def pixmapToDataUrl(self, pix):
        '''
        @param: pix QPixmap
        @return: QUrl
        '''
        pass

    def dpiAwarePixmap(self, path):
        '''
        @param: path QString
        @return: QPixmap
        '''
        pass

    def readAllFileContents(self, filename):
        '''
        @param: filename QString
        @return: QString
        '''
        return self.readAllFileByteContents(filename).decode('utf8')

    def readAllFileByteContents(self, filename):
        '''
        @note: filename maybe resource file like ':/data/bookmarks.json', so must use QFile to read
        @param: filename QString
        @return: QByteArray
        '''
        file_ = QFile(filename)
        if filename and file_.open(QFile.ReadOnly):
            a = file_.readAll()
            file_.close()
            return a.data()
        return b''

    def centerWidgetOnScreen(self, widget):
        pass

    def centerWidgetToParent(self, widget, parent):
        pass

    def removeRecursively(self, filePath):
        pass

    def copyRecursively(self, sourcePath, targetPath):
        pass

    def samePartOfStrings(self, one, other):
        '''
        @param: one QString
        @param: other QString
        @return: QString
        '''
        pass

    def urlEncodeQueryString(self, url):
        '''
        @param: url QUrl
        @return: QString
        '''
        result = url.toString(QUrl.RemoveQuery | QUrl.RemoveFragment)
        if url.hasQuery():
            result += '?' + url.query(QUrl.FullyEncoded)
        if url.hasFragment():
            result += '#' + url.fragment(QUrl.FullyEncoded)
        result.replace(' ', '%20')
        return result

    def fromPunycode(self, str0):
        '''
        @param: str0 QString
        @return: QString
        '''
        pass

    def eascapeSqlGlobString(self, urlString):
        '''
        @param: urlString QString
        @return: QString
        '''
        pass

    def ensureUniqueFilename(self, name, appendFormat="(%s)"):
        pass

    def getFileNameFromUrl(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def filterCharsFromFilename(self, filename):
        value = filename
        value = value.replace('/', '-')
        for delch in ['\\', ':', '*', '?', '"', '<', '>', '|']:
            value = value.replace(delch, '')
        return value

    def lastPathForFileDialog(self, dialogName, fallbackPath):
        pass

    def saveLastPathForFileDialog(self, dialogName, path):
        '''
        @params: QString
        '''
        pass

    def alignTextToWidth(self, string, text, metrics, width):
        '''
        @param: string QString
        @param: text QString
        @param: metrics QFontMetrics
        @param: width int
        @return: QString
        '''
        pass

    def fileSizeToString(self, size):
        '''
        @param: size qint64
        @return: QString
        '''
        if size < 0:
            return _('Unknown size')

        _size = size / 1024.0  # KB
        if _size < 1000:
            if _size > 1:
                return '%s KB' % int(_size)
            else:
                return '1 KB'

        _size /= 1024  # MB
        if _size < 1000:
            return '%.1f MB' % _size

        _size /= 1024  # GB
        return '%.2f GB' % _size

    def createPixmapForSite(self, icon, title, url):
        '''
        @param: icon QIcon
        @param: title QString
        @param: url QString
        @return: QPixmap
        '''
        pass

    def applyDirectionToPage(self, pageContents):
        '''
        @param: pageContents QString
        @return: QStirng
        '''
        pass

    def truncatedText(self, text, size):
        '''
        @param: text QString
        @param: size int
        @return: QString
        '''
        if len(text) > size:
            return text[:size] + '..'
        return text

    def resolveFromPath(self, name):
        '''
        @param: name QString
        @return: QString
        '''
        pass

    def splitCommandArguments(self, command):
        '''
        @param: command QString
        @return: QStringList
        '''
        pass

    def startExternalProcess(self, executable, args):
        '''
        @param: executable QString
        @param: args QString
        @return: bool
        '''
        pass

    def roundedRect(self, rect, radius):
        '''
        @param: rect QRect
        @param: radius int
        @return: QRegion
        '''
        pass

    def iconFromFileName(self, fileName):
        '''
        @param: fileName QString
        @return: QIcon
        '''
        pass

    def isUtf8(self, string):
        '''
        @param: string const char* (bytes)
        @return: bool
        '''
        pass

    def containsSpace(self, str0):
        '''
        @return: bool
        '''
        pass

    # QFileDialog static functions that members last used directory
    def getExistingDirectory(self, name, parent=None, caption='', dir_='',
            options=QFileDialog.ShowDirsOnly):
        '''
        @param: name QString
        @param: parent QWidget
        @param: caption QString
        @param: dir_ QString
        @param: options QFileDialog.Options
        @return: QString
        '''
        pass

    def getFileName(self, path):
        if isfile(path):
            return basename(path)
        if isdir(path):
            return ''
        if pathexists(dirname(path)):
            return basename(path)
        return ''

    def getOpenFileName(self, name, parent=None, caption='', dir_='', filter_='',
            selectedFilter='', options=QFileDialog.Options()):
        '''
        @param: name QString
        @param: parent QWidget
        @param: caption QString
        @param: dir_ QString
        @param: filter_ QString
        @param: selectedFilter QString TODO: this is an output parameter
        @param: options QFileDialog::Options
        '''
        settings = Settings()
        settings.beginGroup('FileDialogPaths')
        lastDir = settings.value(name, '')
        fileName = self.getFileName(dir_)
        if not lastDir:
            lastDir = dir_
        else:
            lastDir = pathjoin(lastDir, fileName)
        path, selectedFilter = QFileDialog.getOpenFileName(parent, caption,
                lastDir, filter_, selectedFilter, options)
        if path:
            settings.setValue(name, abspath(path))
        settings.endGroup()
        return path

    def getOpenFileNames(self, name, parent=None, caption='', dir_='',
            filter_='', selectedFilter='', options=QFileDialog.Options()):
        '''
        @param: name QString
        @param: parent QWidget
        @param: caption QString
        @param: dir_ QString
        @param: filter_ QString
        @param: selectedFilter QString TODO: this is an output parameter
        @param: options QFileDialog::Options
        @return: QStringList
        '''
        settings = Settings()
        settings.beginGroup('FileDialogPaths')

        lastDir = settings.value(name, '')
        fileName = self.getFileName(dir_)

        if not lastDir:
            lastDir = dir_
        else:
            lastDir = pathjoin(lastDir, fileName)

        paths, selectedFilter = QFileDialog.getOpenFileNames(parent, caption,
            lastDir, filter_, selectedFilter, options)

        if paths:
            settings.setValue(name, QFileInfo(paths[0]).absolutePath())

        settings.endGroup()
        return paths

    def getSaveFileName(self, name, parent=None, caption='', dir_='',
            filter_='', selectedFilter='', options=QFileDialog.Options()):
        '''
        @param: name QString
        @param: parent QWidget
        @param: caption QString
        @param: dir_ QString
        @param: filter_ QString
        @param: selectedFilter QString TODO: this is an output parameter
        @param: options QFileDialog::Options
        @return: QString
        '''
        settings = Settings()
        settings.beginGroup('FileDialogPaths')

        lastDir = settings.value(name, '')
        fileName = self.getFileName(dir_)

        if not lastDir:
            lastDir = dir_
        else:
            lastDir = pathjoin(lastDir, fileName)

        path, selectedFilter = QFileDialog.getSaveFileName(parent, caption,
            lastDir, filter_, selectedFilter, options)

        if path:
            settings.setValue(name, QFileInfo(path).absolutePath())

        settings.endGroup()
        return path

    def matchDomain(self, pattern, domain):
        '''
        @note: Matches domain (assumes both pattern and domain not starting with dot)
        @param: pattern QString, domain to be matched
        @param: domain QString, site domain
        @return: bool
        '''
        if pattern == domain:
            return True

        if not domain.endswith(pattern):
            return False

        index = domain.index(pattern)

        return index > 0 and domain[index-1] == '.'

    def actionShortcut(self, shortcut, fallBack, shortcutRtl=QKeySequence(),
            fallbackRtl=QKeySequence()):
        '''
        @param: shortcut QKeySequence
        @param: fallBack QKeySequence
        @param: shortcutRtl QKeySequence
        @param: fallbackRtl QKeySequence
        @return: QKeySequence
        '''
        if QApplication.isRightToLeft() and (not shortcutRtl.isEmpty() or not fallbackRtl.isEmpty()):
            if shortcutRtl.isEmpty():
                return fallbackRtl
            else:
                return shortcutRtl

        if not shortcut:
            return fallBack
        else:
            return shortcut

    def operatingSystem(self):
        '''
        @return: QString
        '''
        pass

    def cpuArchitecture(self):
        '''
        @return: QString
        '''
        pass

    def operatingSystemLong(self):
        '''
        @return: QString
        '''
        pass

    def setWmClass(self, name, widget):
        '''
        @param: name QString
        @param: widget QWidget
        '''
        pass

    def containsIndex(self, container, index):
        return index >= 0 and len(container) > index

    def paintDropIndicator(self, widget, rect):
        '''
        @param: widget QWidget
        @param: rect QRect
        '''
        # Modified code from KFilePlacesView
        color = widget.palette().brush(QPalette.Normal, QPalette.Highlight).color()
        x = (rect.left() - rect.right()) / 2
        thickness = int(rect.width() / 2.0 + 0.5)
        alpha = 255
        alphaDec = alpha / (thickness + 1)
        p = QStylePainter(widget)
        for idx in range(thickness):
            color.setAlpha(alpha)
            alpha -= alphaDec
            p.setPen(color)
            p.drawLine(x-idx, rect.top(), x-idx, rect.bottom())
            p.drawLine(x+idx, rect.top(), x+idx, rect.bottom())
