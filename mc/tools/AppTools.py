from os.path import isfile, isdir, dirname, basename, abspath
from os.path import join as pathjoin, exists as pathexists
from PyQt5.Qt import QFileDialog
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QPalette
from PyQt5.Qt import QStylePainter
from PyQt5.Qt import QFile
from PyQt5.Qt import QUrl
from PyQt5.Qt import QFileInfo
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QBuffer
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QIcon
from PyQt5.Qt import QFileIconProvider
from PyQt5.Qt import QRegion
from PyQt5.Qt import QRect
from PyQt5.Qt import QSize
from PyQt5.Qt import QProcess
from PyQt5.Qt import QPoint
from PyQt5.Qt import QSysInfo
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from mc.app.Settings import Settings
from mc.common.designutil import Singleton
from mc.app.DataPaths import DataPaths

class AppTools(Singleton):

    def pixmapToByteArray(self, pix):
        '''
        @param: pix QPixmap
        @return: QByteArray
        '''
        bytes_ = QByteArray()
        buffer_ = QBuffer(bytes_)
        buffer_.open(QIODevice.WriteOnly)
        if pix.save(buffer_, 'PNG'):
            return buffer_.buffer().toBase64()
        return QByteArray()

    def pixmapFromByteArray(self, data):
        '''
        @param: data QByteArray
        @return: QPixmap
        '''
        pixmap = QPixmap()
        bArray = QByteArray.fromBase64(data)
        pixmap.loadFromData(bArray)

        return pixmap

    def pixmapToDataUrl(self, pix):
        '''
        @param: pix QPixmap
        @return: QUrl
        '''
        data = self.pixmapToByteArray(pix)
        if not data:
            return QUrl()
        else:
            return QUrl('data:image/png;base64,' + data.data().decode())

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
        # QRect
        screen = QApplication.desktop().screenGeometry(widget)
        size = widget.geometry()
        widget.move((screen.width() - size.width()) / 2,
                (screen.height() - size.height()) / 2)

    def centerWidgetToParent(self, widget, parent):
        '''
        @brief: Very, very, very simplified QDialog.adjustPosition from qdialog.cpp
        '''
        if not parent or not widget:
            return

        p = QPoint()
        parent = parent.window()
        # QPoint
        pp = parent.mapToGlobal(QPoint(0, 0))
        p = QPoint(pp.x() + parent.width() / 2, pp.y() + parent.height() / 2)
        p = QPoint(p.x() - widget.width() / 2, p.y() - widget.height() / 2 - 20)

        widget.move(p)

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

    def escapeSqlGlobString(self, urlString):
        '''
        @param: urlString QString
        @return: QString
        '''
        urlString = urlString.replace('[', "[[")
        urlString = urlString.replace(']', "[]]")
        urlString = urlString.replace("[[", "[[]")
        urlString = urlString.replace('*', "[*]")
        urlString = urlString.replace('?', "[?]")
        return urlString

    def ensureUniqueFilename(self, name, appendFormat="(%s)"):
        pass

    def getFileNameFromUrl(self, url):
        '''
        @param: url QUrl
        '''
        fileName = url.toString(QUrl.RemoveFragment | QUrl.RemoveQuery |
                QUrl.RemoveScheme | QUrl.RemovePort)

        fileName = basename(fileName.rstrip('/\\'))
        fileName = self.filterCharsFromFilename(fileName)

        if not fileName:
            fileName = self.filterCharsFromFilename(url.host())

        return fileName

    def filterCharsFromFilename(self, fileName):
        value = fileName
        value = value.replace('/', '-')
        for delch in ['\\', ':', '*', '?', '"', '<', '>', '|']:
            value = value.replace(delch, '')
        return value

    def lastPathForFileDialog(self, dialogName, fallbackPath):
        settings = Settings()
        settings.beginGroup('LastFileDialogsPaths')
        path = settings.value('FileDialogs/' + dialogName)
        settings.endGroup()

        if not path:
            return fallbackPath
        return path

    def saveLastPathForFileDialog(self, dialogName, path):
        '''
        @params: QString
        '''
        if not path:
            return

        settings = Settings()
        settings.beginGroup('LastFileDialogsPaths')
        settings.setValue('FileDialogs/' + dialogName, path)
        settings.endGroup()

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
        direction = "ltr"
        right_str = "right"
        left_str = "left"

        if QApplication.isRightToLeft():
            direction = "rtl"
            right_str = "left"
            left_str = "right"

        pageContents = pageContents.replace("%DIRECTION%", direction) \
            .replace("%RIGHT_STR%", right_str) \
            .replace("%LEFT_STR%", left_str)

        return pageContents

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
        arguments = self.splitCommandArguments(args)

        success = QProcess.startDetached(executable, arguments)

        if not success:
            info = '<ul><li><b>%s</b>%s</li><li><b>%s</b>%s</li></ul>' % \
                (_('Executable: '), executable, _('Arguments:'), ' '.join(arguments))
            QMessageBox.critical(None, _('Cannot start external program'),
                    _('Cannot start external program! %s') % info)

        return success

    def roundedRect(self, rect, radius):
        '''
        @param: rect QRect
        @param: radius int
        @return: QRegion
        '''
        region = QRegion()

        # middle and borders
        region += rect.adjusted(radius, 0, -radius, 0)
        region += rect.adjusted(0, radius, 0, -radius)

        # top left
        corner = QRect(rect.topLeft(), QSize(radius * 2, radius * 2))
        region += QRegion(corner, QRegion.Ellipse)

        # top right
        corner.moveTopRight(rect.topRight())
        region += QRegion(corner, QRegion.Ellipse)

        # bottom left
        corner.moveBottomLeft(rect.bottomLeft())
        region += QRegion(corner, QRegion.Ellipse)

        # bottom right
        corner.moveBottomRight(rect.bottomRight())
        region += QRegion(corner, QRegion.Ellipse)

        return region

    _s_iconCache = {}
    def iconFromFileName(self, fileName):
        '''
        @param: fileName QString
        @return: QIcon
        '''
        tempInfo = QFileInfo(fileName)
        suffix = tempInfo.suffix()
        if suffix in self._s_iconCache:
            return self._s_iconCache[suffix]

        iconProvider = QFileIconProvider()
        tempFile = DataPaths.path(DataPaths.Temp) + '/XXXXXX.' + suffix
        tempFile.open()
        tempInfo.setFile(tempFile.fileName())

        icon = QIcon(iconProvider.icon(tempInfo))
        self._s_iconCache[suffix] = icon

    def isUtf8(self, string):
        '''
        @param: string const char* (bytes)
        @return: bool
        '''
        if isinstance(string, QByteArray):
            string = string.data()
        assert(isinstance(string, bytes))
        try:
            string.decode('utf8')
            return True
        except UnicodeDecodeError:
            return False

    def containsSpace(self, str0):
        '''
        @return: bool
        '''
        return len(str0.split()) > 1

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
        return QSysInfo.currentCpuArchitecture()

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
        x = (rect.left() + rect.right()) / 2
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
