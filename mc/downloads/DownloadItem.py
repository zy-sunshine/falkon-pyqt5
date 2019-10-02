from os import system
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.Qt import QTime
from PyQt5.Qt import QUrl
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIcon
from PyQt5.Qt import Qt
from PyQt5.Qt import QFileIconProvider
from PyQt5.Qt import QStyle
from PyQt5.Qt import QFileInfo
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QApplication
from PyQt5.Qt import QDesktopServices
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineDownloadItem
from os.path import join as pathjoin, exists as pathexists, abspath
from mc.common import const
from mc.common.globalvars import gVar

class DownloadItem(QWidget):
    DEBUG = True
    def __init__(self, item, downloadItem, path, fileName, openFile, manager):
        '''
        @param: item QListWidgetItem
        @param: downloadItem QWebEngineDownloadItem
        @param: path QString
        @param: fileName QString
        @param: openFile bool
        @param: manager DownloadManager
        '''
        super().__init__()
        self._ui = uic.loadUi('mc/downloads/DownloadItem.ui', self)
        self._item = item  # QListWidgetItem
        self._download = downloadItem  # QWebEngineDownloadItem
        self._path = path
        self._fileName = fileName
        self._downTimer = QTime()
        self._remTime = QTime()
        self._downUrl = QUrl()
        self._openFile = openFile

        self._downloading = False
        self._downloadStopped = False
        self._currSpeed = 0.0
        self._received = downloadItem.receivedBytes()
        self._total = downloadItem.totalBytes()

        if self.DEBUG:
            print('DEBUG: %s::__init__ %s %s %s %s' % (self.__class__.__name__,
                item, downloadItem, path, fileName))

        self.setMaximumWidth(525)

        self._ui.button.setPixmap(QIcon.fromTheme('process-stop').pixmap(20, 20))
        self._ui.fileName.setText(self._fileName)
        self._ui.downloadInfo.setText(_('Remaining time unavailable'))

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._customContextMenuRequested)
        self._ui.button.clicked.connect(self._stop)
        manager.resized.connect(self._parentResized)

    def isDownloading(self):
        '''
        @return: bool
        '''
        return self._downloading

    def isCancelled(self):
        '''
        @return: bool
        '''
        self._ui.downloadInfo.text().startswith(_('Cancelled'))

    def remainingTime(self):
        '''
        @return: QTime
        '''
        return self._remTime

    def currentSpeed(self):
        '''
        @return: double
        '''
        return self._currSpeed

    def progress(self):
        '''
        @return: int
        '''
        return self._ui.progressBar.value()

    def setDownTimer(self, timer):
        '''
        @param: timer QTime
        '''
        self._downTimer = timer

    def startDownloading(self):
        self._download.finished.connect(self._finished)
        self._download.downloadProgress.connect(self._downloadProgress)

        self._downloading = True
        if self._downTimer.elapsed() < 1:  # TODO: ?
            self._downTimer.start()

        self._updateDownloadInfo(0, self._download.receivedBytes(), self._download.totalBytes())

        if const.OS_LINUX:
            # QFileIconProvider uses only suffix on Linux
            iconProvider = QFileIconProvider()
            # QIcon
            fileIcon = iconProvider.icon(QFileInfo(self._fileName))
            if not fileIcon.isNull():
                self._ui.fileIcon.setPixmap(fileIcon.pixmap(30))
            else:
                self._ui.fileIcon.setPixmap(self.style().standardIcon(QStyle.SP_FileIcon).pixmap(30))
        else:
            self._ui.fileIcon.hide()

    @classmethod
    def remaingTimeToString(cls, time):
        '''
        @param: time QTime
        '''
        if time < QTime(0, 0, 10):
            return _('few seconds')
        elif time < QTime(0, 1):
            return _('%s seconds') % time.second()
        elif time < QTime(1, 0):
            return _('%s minutes') % time.minute()
        else:
            return _('%s hours') % time.hour()

    @classmethod
    def currentSpeedToString(cls, speed):
        '''
        @param: speed double
        '''
        if speed < 0:
            return _('Unknown speed')

        speed /= 1024  # kB
        if speed < 1000:
            return '%s kB/s' % int(speed)

        speed /= 1024  # MB
        if speed < 1000:
            return '%.2f MB/s' % speed

        speed /= 1024  # GB
        return '%.2f GB/s' % speed

    # Q_SIGNALS:
    deleteItem = pyqtSignal('PyQt_PyObject')  # DonwloadItem
    downloadFinished = pyqtSignal(bool)  # bool success

    # private Q_SLOTS:
    def _parentResized(self, size):
        '''
        @param: size QSize
        '''
        if size.width() < 200:
            return
        self.maximumWidth(size.width())

    def _finished(self):
        if self.DEBUG:
            print('DEBUG: %s::_finished' % self.__class__.__name__)

        success = False
        host = self._download.url().host()

        state = self._download.state()
        if state == QWebEngineDownloadItem.DownloadCompleted:
            success = True
            self._ui.downloadInfo.setText(_('Done - %s (%s)') %
                (host, QDateTime.currentDateTime().toString(Qt.DefaultLocaleShortDate)))
        elif state == QWebEngineDownloadItem.DownloadInterrupted:
            self._ui.donwloadInfo.setText(_('Error - %s') % host)
        elif state == QWebEngineDownloadItem.DownloadCancelled:
            self._ui.downloadInfo.setText(_('Cancelled = %s') % host)

        self._ui.progressBar.hide()
        self._ui.button.hide()
        self._ui.frame.hide()

        self._item.setSizeHint(self.sizeHint())
        self._downloading = False

        if success and self._openFile:
            self.__openFile()

        self.downloadFinished.emit(True)

    def _downloadProgress(self, received, total):
        '''
        @param: received qint64
        @param: total qint64
        '''
        if self.DEBUG:
            print('DEBUG: %s::_downloadProgress %s %s' % (self.__class__.__name__,
                received, total))
        currentValue = 0
        totalValue = 0
        if total > 0:
            currentValue = received * 100 / total
            totalValue = 100
        self._ui.progressBar.setValue(currentValue)
        self._ui.progressBar.setMaximum(totalValue)
        self._currSpeed = received * 1000.0 / self._downTimer.elapsed()
        self._received = received
        self._total = total

        self._updateDownloadInfo(self._currSpeed, self._received, self._total)

    def _stop(self):
        if self.DEBUG:
            print('DEBUG: %s::_stop' % self.__class__.__name__)
        self._downloadStopped = True
        self._ui.progressBar.hide()
        self._ui.button.hide()
        self._item.setSizeHint(self.sizeHint())
        self._ui.downloadInfo.setText(_('Cancelled - %s') % self._download.url().host())
        self._download.cancel()
        self._downloading = False

        self.downloadFinished.emit(False)

    def __openFile(self):
        if self._downloading:
            return
        fpath = pathjoin(self._path, self._fileName)
        if pathexists(fpath):
            QDesktopServices.openUrl(QUrl.fromLocalFile(abspath(fpath)))
        else:
            QMessageBox.warning(self._item.listWidget().parentWidget(),
                _("Not found"), _("Sorry, the file \n %s \n was not found!") % abspath(fpath))

    def _openFolder(self):
        if const.OS_WIN:
            winFileName = '%s/%s' % (self._path, self._fileName)

            if self._downloading:
                winFileName += '.download'

            winFileName = winFileName.replace('/', '\\')
            shExArg = '/e,/select,"%s"' % winFileName
            system('explorer.exe ' + shExArg)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._path))

    def _customContextMenuRequested(self, pos):
        '''
        @param: pos QPoint
        '''
        menu = QMenu()
        menu.addAction(QIcon.fromTheme('document-open'), _('Open File'), self.__openFile)

        menu.addAction(_('Open Folder'), self._openFolder)
        menu.addSeparator()
        menu.addAction(QIcon.fromTheme('edit-copy'), _('Copy Download Link'), self._copyDownloadLink)
        menu.addSeparator()
        menu.addAction(QIcon.fromTheme('process-stop'), _('Cancel downloading'),
            self._stop).setEnabled(self._downloading)
        menu.addAction(QIcon.fromTheme('list-remove'), _('Remove From List'),
            self._clear).setEnabled(not self._downloading)

        if self._downloading or self._ui.downloadInfo.text().startswith(_('Cancelled')) or \
                self._ui.downloadInfo.text().startswith(_('Error')):
            menu.actions()[0].setEnabled(False)
        menu.exec_(self.mapToGlobal(pos))

    def _clear(self):
        self.deleteItem.emit(self)

    def _copyDownloadLink(self):
        QApplication.clipboard().setText(self._downUrl.toString())

    # private:
    def _updateDownloadInfo(self, currSpeed, received, total):
        '''
        @param: currSpeed double
        @param: received qint64
        @param: total qint64
        '''
        if self.DEBUG:
            print('DEBUG: %s::_updateDownloadInfo %s %s %s' % (self.__class__.__name__,
                currSpeed, received, total))
        #            QString          QString       QString     QString
        #          | m_remTime |   |m_currSize|  |m_fileSize|  |m_speed|
        # Remaining 26 minutes -     339MB of      693 MB        (350kB/s)
        if currSpeed == 0: currSpeed = 1
        estimatedTime = ((total - received) / 1024) / (currSpeed / 1024)
        speed = self.currentSpeedToString(currSpeed)
        # We have QString speed now

        time = QTime(0, 0, 0)
        time = time.addSecs(estimatedTime)
        remTime = self.remaingTimeToString(time)
        self._remTime = time

        currSize = gVar.appTools.fileSizeToString(received)
        fileSize = gVar.appTools.fileSizeToString(total)

        if fileSize == _('Unkown size'):
            self._ui.downloadInfo.setText(_('%s - unkown size (%s)') % (currSize, speed))
        else:
            self._ui.downloadInfo.setText(_('Remaining %s - %s of %s (%s)') % (
                remTime, currSize, fileSize, speed))

    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        self.__openFile()
        event.accept()
