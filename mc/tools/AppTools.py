from os import environ
from os import readlink
from os.path import pathsep
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
from PyQt5.Qt import QRectF
from PyQt5.Qt import QSize
from PyQt5.Qt import QProcess
from PyQt5.Qt import QPoint
from PyQt5.Qt import QSysInfo
from PyQt5.Qt import QDir
from PyQt5.Qt import Qt
from PyQt5.Qt import QPainter
from PyQt5.Qt import QPen
from PyQt5.Qt import QPainterPath
from PyQt5.Qt import QGuiApplication
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from mc.app.Settings import Settings
from mc.common.designutil import Singleton
from mc.app.DataPaths import DataPaths
from mc.common import const
from mc.common.globalvars import gVar

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
        icon = QIcon(path)
        if not icon.availableSizes():
            return QPixmap(path)
        return icon.pixmap(icon.availableSizes()[0])

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
        '''
        @param: filePath QString
        '''
        fileInfo = QFileInfo(filePath)
        if not fileInfo.exists() and not fileInfo.isSymLink():
            return
        if fileInfo.isDir() and not fileInfo.isSymLink():
            dir_ = QDir(filePath)
            dir_ = dir_.canonicalPath()
            if dir_.isRoot() or dir_.path() == QDir.home().canonicalPath():
                print('CRITICAL: Attempt to remove root/home directory', dir_)
                return False
            fileNames = dir_.entryList(QDir.Files | QDir.Dirs | QDir.NoDotAndDotDot |
                    QDir.Hidden | QDir.System)
            for fileName in fileNames:
                if not self.removeRecursively(filePath + '/' + fileName):
                    return False
            if not QDir.root().rmdir(dir_.path()):
                return False
        elif not QFile.remove(filePath):
            return False
        return True

    def copyRecursively(self, sourcePath, targetPath):
        srcFileInfo = QFileInfo(sourcePath)
        if srcFileInfo.isDir() and not srcFileInfo.isSymLink():
            targetDir = QDir(targetPath)
            targetDir.cdUp()
            if not targetDir.mkdir(QFileInfo(targetPath).fileName()):
                return False
            fileNames = QDir(sourcePath).entryList(QDir.Files | QDir.Dirs | QDir.NoDotAndDotDot |
                    QDir.Hidden | QDir.System)
            for fileName in fileNames:
                newSourcePath = sourcePath + '/' + fileName
                newTargetPath = targetPath + '/' + fileName
                if not self.copyRecursively(newSourcePath, newTargetPath):
                    return False
        elif not const.OS_WIN and srcFileInfo.isSymLink():
            linkPath = readlink(sourcePath)
            return QFile.link(linkPath, targetPath)
        elif not QFile.copy(sourcePath, targetPath):
            return False
        return True

    def samePartOfStrings(self, one, other):
        '''
        @brief: Finds same part of @one in @other from the beginning
        @param: one QString
        @param: other QString
        @return: QString
        '''
        maxSize = min(len(one), len(other))
        if maxSize <= 0:
            return ''

        idx = 0
        while one[idx] == other[idx]:
            idx += 1
            if idx == maxSize:
                break
        return one[:idx]

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
        if not str0.startswith('xn--'):
            return str0

        # QUrl::fromAce will only decode domains from idn whitelist
        decoded = QUrl.fromAce(str0.encode() + b'.org')
        return decoded[:len(decoded) - 4]

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
        assert('%s' in appendFormat)

        info = QFileInfo(name)
        if not info.exists():
            return name

        # QDir
        dir_ = info.absoluteDir()
        # QString
        fileName = info.fileName()

        idx = 1
        while info.exists():
            file_ = fileName
            index = file_.rfind('.')
            appendString = appendFormat % idx
            if index == -1:
                file_ += appendString
            else:
                file_ = file_[:index] + appendString + file_[index:]
            info.setFile(dir_, file_)
            idx += 1

        return info.absoluteFilePath()

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
        @brief: fill repeat string with text seperator to width size according metrics
        @param: string QString
        @param: text QString
        @param: metrics QFontMetrics
        @param: width int
        @return: QString
        '''
        pos = 0
        returnString = ''

        while pos <= len(string):
            part = string[pos:]
            elidedLine = metrics.elidedText(part, Qt.ElideRight, width)

            if not elidedLine:
                break

            if len(elidedLine) != len(part):
                elidedLine = elidedLine[:len(elidedLine) - 3]

            if returnString:
                returnString += text

            returnString += elidedLine
            pos += len(elidedLine)

        return returnString

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
        fontMetrics = QApplication.fontMetrics()
        padding = 4
        text = len(title) > len(url) and title or url
        maxWidth = fontMetrics.width(text) + 3 * padding + 16
        width = min(maxWidth, 150)
        height = fontMetrics.height() * 2 + fontMetrics.leading() + 2 * padding

        pixelRatio = gVar.app.devicePixelRatio()
        pixmap = QPixmap(width * pixelRatio, height * pixelRatio)
        pixmap.setDevicePixelRatio(pixelRatio)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)

        path = QPainterPath()
        path.addRect(QRectF(0, 0, width, height))

        painter.fillPath(path, Qt.white)
        painter.drawPath(path)

        # Draw icon
        iconRect = QRect(padding, 0, 16, height)
        icon.paint(painter, iconRect)

        # Draw title
        titleRect = QRectF(iconRect.right() + padding, padding,
                width - padding - iconRect.right(), fontMetrics.height())
        painter.drawText(titleRect, fontMetrics.elidedText(title, Qt.ElideRight, titleRect.width()))

        # Draw url
        urlRect = QRectF(titleRect.x(), titleRect.bottom() + fontMetrics.leading(),
                titleRect.width(), titleRect.height())
        painter.setPen(QApplication.palette().color(QPalette.Link))
        painter.drawText(urlRect, fontMetrics.elidedText(url, Qt.ElideRight, urlRect.width()))

        return pixmap

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
        path = environ['PATH'].strip()

        if not path:
            return ''

        for item in path.split(pathsep):
            item = item.strip()
            if not item: continue
            d = QDir(item)
            if d.exists(name):
                return d.absoluteFilePath(name)

        return ''

    def _s_isQuote(self, c):
        return c == '"' or c == '\''

    def splitCommandArguments(self, command):  # noqa C901
        '''
        @note: Function splits command line into arguments
            eg. /usr/bin/foo -o test -b "bar bar" -s="sed sed"
            => '/usr/bin/foo' '-o' 'test' '-b' 'bar bar' '-s=sed sed'
        @param: command QString
        @return: QStringList
        '''
        line = command.strip()

        if not line:
            return []

        SPACE = ' '
        EQUAL = '='
        BSLASH = '\\'
        QUOTE = '"'
        r = []

        equalPos = -1  # Position of = in opt="value"
        startPos = self._s_isQuote(line[0]) and 1 or 0
        inWord = not self._s_isQuote(line[0])
        inQuote = not inWord

        if inQuote:
            QUOTE = line[0]

        strlen = len(line)
        for idx in range(strlen):
            c = line[idx]

            if inQuote and c == QUOTE and idx > 0 and line[idx - 1] != BSLASH:
                str_ = line[startPos: idx-startPos]
                if equalPos > -1:
                    pos = equalPos-startPos+1
                    str_ = str_[:pos] + str_[pos+1:]

                inQuote = False
                if str_:
                    r += str_
                continue
            elif not inQuote and self._s_isQuote(c):
                inQuote = True
                QUOTE = c

                if not inWord:
                    startPos = idx + 1
                elif idx > 0 and line[idx-1] == EQUAL:
                    equalPos = idx - 1

            if inQuote:
                continue

            if inWord and (c == SPACE or idx == strlen - 1):
                len_ = (idx == strlen - 1) and -1 or idx - startPos
                str_ = line[startPos: len_]

                inWord = False
                if str_:
                    r += str_
            elif not inWord and c != SPACE:
                inWord = True
                startPos = idx

        # Unmatched quote
        if inQuote:
            return []

        return r

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
        settings = Settings()
        settings.beginGroup('FileDialogPaths')

        lastDir = settings.value(name, dir_)

        path = QFileDialog.getExistingDirectory(parent, caption, lastDir, options)

        if path:
            settings.setValue(name, QFileInfo(path).absolutePath())

        settings.endGroup()
        return path

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

    def operatingSystem(self):  # noqa C901
        '''
        @return: QString
        '''
        if const.OS_MACOS:
            str_ = 'Mac OS X'

            # # SInt32
            # majorVersion = 0
            # # SInt32
            # minorVersion = 0

            #if (Gestalt(gestaltSystemVersionMajor, &majorVersion) == noErr &&
            #       Gestalt(gestaltSystemVersionMinor, &minorVersion) == noErr) {
            #    str_.append(QString(" %1.%2").arg(majorVersion).arg(minorVersion));
            #}
            return str_
        if const.OS_LINUX:
            return 'Linux'
        if const.OS_UNIX:
            return 'Unix'
        if const.OS_WIN:
            str_ = 'Windows'

            ver = QSysInfo.windowsVersion()
            if ver == QSysInfo.WV_NT:
                str_ += ' NT'
            elif ver == QSysInfo.WV_2000:
                str_ += ' 2000'
            elif ver == QSysInfo.WV_XP:
                str_ += ' XP'
            elif ver == QSysInfo.WV_2003:
                str_ += ' XP Pro x64'
            elif ver == QSysInfo.WV_VISTA:
                str_ += ' Vista'
            elif ver == QSysInfo.WV_WINDOWS7:
                str_ += ' 7'
            elif ver == QSysInfo.WV_WINDOWS8:
                str_ += ' 8'
            elif ver == QSysInfo.WV_WINDOWS8_1:
                str_ += ' 8.1'
            elif ver == QSysInfo.WV_WINDOWS10:
                str_ += ' 10'

            return str_

    def cpuArchitecture(self):
        '''
        @return: QString
        '''
        return QSysInfo.currentCpuArchitecture()

    def operatingSystemLong(self):
        '''
        @return: QString
        '''
        arch = self.cpuArchitecture()
        if not arch:
            return self.operatingSystem()
        return self.operatingSystem() + ' ' + arch

    def setWmClass(self, name, widget):
        '''
        @param: name QString
        @param: widget QWidget
        '''
        if const.APP_WS_X11:
            if QGuiApplication.platformName() != 'xcb':
                return

            # TODO: for x11
            #nameData = name.encode()
            #classData = gVar.app.wmClass() and 'App' or gVar.app.wmClass()

            #class_hint = nameData + ' ' + classData

            #xcb_change_property(QX11Info::connection(), XCB_PROP_MODE_REPLACE, widget->winId(),
            #            XCB_ATOM_WM_CLASS, XCB_ATOM_STRING, 8, class_len, class_hint);

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
