from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QBasicTimer
from PyQt5.Qt import QSize
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QTime
from PyQt5.Qt import QStandardPaths
from PyQt5.Qt import Qt
from PyQt5.Qt import QIcon
from PyQt5.Qt import QUrl
from PyQt5.Qt import QShortcut
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QFileInfo
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWinExtras import QWinTaskbarButton
from PyQt5.QtWebEngineWidgets import QWebEngineDownloadItem
from PyQt5.QtWinExtras import QtWin
from os.path import join as pathjoin, basename
from mc.common.globalvars import gVar
from mc.common import const
from mc.app.DataPaths import DataPaths
from mc.app.Settings import Settings
from mc.common.qtutil import qtUtil
from .DownloadOptionsDialog import DownloadOptionsDialog
from .DownloadItem import DownloadItem

class DownloadManager(QWidget):

    # DownloadOption
    OpenFile = 0
    SaveFile = 1
    ExternalManager = 2
    NoOption = 3

    class DownloadInfo:
        def __init__(self, page):
            '''
            @param: page WebPage
            '''
            self.page = page  # WebPage
            self.suggestedFileName = ''

            self.askWhatToDo = True
            self.forceChoosingPath = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = None  # Ui::DownloadManager
        self._timer = QBasicTimer()

        self._lastDownloadPath = ''
        self._downloadPath = ''
        self._useNativeDialog = False
        self._isClosing = False
        self._closeOnFinish = False
        self._activeDownloadsCount = 0

        self._useExternalManager = False
        self._externalExecutable = ''
        self._externalArguments = ''

        self._lastDownloadOption = self.NoOption  # DownloadOption

        self._taskbarButton = None  # QPointer<QWinTaskbarButton>

        self._ui = uic.loadUi('mc/downloads/DownloadManager.ui', self)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowMaximizeButtonHint)
        if const.OS_WIN:
            if QtWin.isCompositionEnabled():  # TODO: ?
                QtWin.extendFrameIntoClientArea(self, -1, -1, -1, -1)
        self._ui.clearButton.setIcon(QIcon.fromTheme('edit-clear'))
        gVar.appTools.centerWidgetOnScreen(self)

        self._ui.clearButton.clicked.connect(self._clearList)

        clearShortcut = QShortcut(QKeySequence('CTRL+L'), self)
        clearShortcut.activated.connect(self._clearList)

        self.loadSettings()

        gVar.appTools.setWmClass('Download Manager', self)

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup("DownloadManager")
        self._downloadPath = settings.value("defaultDownloadPath", '')
        self._lastDownloadPath = settings.value("lastDownloadPath",
            QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        self._closeOnFinish = settings.value("CloseManagerOnFinish", False)
        self._useNativeDialog = settings.value("useNativeDialog",
            const.DEFAULT_DOWNLOAD_USE_NATIVE_DIALOG)

        self._useExternalManager = settings.value("UseExternalManager", False)
        self._externalExecutable = settings.value("ExternalManagerExecutable", '')
        self._externalArguments = settings.value("ExternalManagerArguments", '')
        settings.endGroup()

        if "%d" not in self._externalArguments:
            self._externalArguments += " %d"

    def download(self, downloadItem):  # noqa C901
        '''
        @param: downloadItem QWebEngineDownloadItem
        '''
        downloadTimer = QTime()
        downloadTimer.start()

        self.closeDownloadTab(downloadItem)

        downloadPath = ''
        openFile = False

        fileName = basename(downloadItem.path())

        forceAsk = downloadItem.savePageFormat() != QWebEngineDownloadItem.UnknownSaveFormat \
            or downloadItem.type() == QWebEngineDownloadItem.UserRequested

        if self._useExternalManager:
            self.startExternalManager(downloadItem.url())
        elif forceAsk or not self._downloadPath:
            (
                Open, Save, ExternalManager, SavePage, Unknown
            ) = range(5)
            result = Unknown

            if downloadItem.savePageFormat() != QWebEngineDownloadItem.UnknownSaveFormat:
                # Save Page Requested
                result = SavePage
            elif downloadItem.type() == QWebEngineDownloadItem.UserRequested:
                # Save x as... requested
                result = Save
            else:
                # Ask what to do
                optionsDialog = DownloadOptionsDialog(fileName, downloadItem, gVar.app.activeWindow())
                optionsDialog.showExternalManagerOption(self._useExternalManager)
                optionsDialog.setLastDownloadOption(self._lastDownloadOption)
                result = optionsDialog.exec_()

            if result == Open:
                openFile = True
                downloadPath = gVar.appTools.ensureUniqueFilename(
                    pathjoin(DataPaths.path(DataPaths.Temp), fileName))
                self._lastDownloadOption = self.OpenFile
            elif result == Save:
                downloadPath, selectedFitler = QFileDialog.getSaveFileName(
                    gVar.app.activeWindow(), _('Save file as...'),
                    pathjoin(self._lastDownloadPath, fileName))

                if downloadPath:
                    self._lastDownloadPath = QFileInfo(downloadPath).absolutePath()
                    Settings().setValue('DownloadManager/lastDownloadPath', self._lastDownloadPath)
                    self._lastDownloadOption = self.SaveFile

            elif result == SavePage:
                mhtml = _('MIME HTML Archive (*.mhtml)')
                htmlSingle = _('HTML Page, single (*.html)')
                htmlComplete = _('HTML Page, complete (*.html)')
                filter_ = '%s;;%s;;%s' % (mhtml, htmlSingle, htmlComplete)

                selectedFilter = ''
                downloadPath, selectedFilter = QFileDialog.getSaveFileName(
                    gVar.app.activeWindow(), _('Save page as...'),
                    pathjoin(self._lastDownloadPath, fileName), filter_,
                    selectedFilter)

                if downloadPath:
                    self._lastDownloadPath = QFileInfo(downloadPath).absolutePath()
                    Settings().setValue('DownloadManager/lastDownloadPath', self._lastDownloadPath)
                    self._lastDownloadOption = self.SaveFile

                    format_ = QWebEngineDownloadItem.UnknownSaveFormat

                    if selectedFilter == mhtml:
                        format_ = QWebEngineDownloadItem.MimeHtmlSaveFormat
                    elif selectedFilter == htmlSingle:
                        format_ = QWebEngineDownloadItem.SingleHtmlSaveFormat
                    elif selectedFilter == htmlComplete:
                        format_ = QWebEngineDownloadItem.CompleteHtmlSaveFormat

                    if format_ == QWebEngineDownloadItem.UnknownSaveFormat:
                        downloadItem.setSavePageFormat(format_)

            elif result == ExternalManager:
                self.startExternalManager(downloadItem.url())
                downloadItem.cancel()
            else:
                downloadItem.cancel()
        else:
            downloadPath = gVar.appTools.ensureUniqueFilename(pathjoin(self._downloadPath, fileName))

        if not downloadPath:
            downloadItem.cancel()
            return

        # Set download path ad accept
        downloadItem.setPath(downloadPath)
        downloadItem.accept()

        # Create download item
        listItem = QListWidgetItem(self._ui.list)
        downItem = DownloadItem(listItem, downloadItem, QFileInfo(downloadPath).absolutePath(),
                basename(downloadPath), openFile, self)
        downItem.setDownTimer(downloadTimer)
        downItem.startDownloading()
        downItem.deleteItem.connect(self._deleteItem)
        downItem.downloadFinished.connect(self._downloadFinished)
        self._ui.list.setItemWidget(listItem, downItem)
        listItem.setSizeHint(downItem.sizeHint())
        downItem.show()

        self._activeDownloadsCount += 1
        self.downloadsCountChanged.emit()

    def downloadsCount(self):
        # TODO:
        return 0

    def activeDownloadsCount(self):
        # TODO:
        return 0

    def canClose(self):
        '''
        @return: bool
        '''
        if self._isClosing:
            return True

        isDownloading = False
        for idx in range(self._ui.list.count()):
            downItem = self._ui.list.itemWidget(self._ui.list.item(idx))
            if not downItem:
                continue
            if downItem.isDownloading():
                isDownloading = True
                break

        return not isDownloading

    def useExternalManager(self):
        '''
        @return: bool
        '''
        return self._useExternalManager

    def startExternalManager(self, url):
        '''
        param: url QUrl
        '''
        arguments = self._externalArguments
        arguments.replace('%d', url.toEncoded())

        gVar.appTools.startExternalProcess(self._externalExecutable, arguments)
        self._lastDownloadOption = self.ExternalManager

    def setLastDownloadPath(self, lastPath):
        self._lastDownloadPath = lastPath

    def setLastDownloadOption(self, option):
        self._lastDownloadOption = option

    # public Q_SLOTS:
    def show(self):
        self._timer.start(500, self)

        super().show()
        self.raise_()
        self.activateWindow()

    # private Q_SLOTS:
    def _clearList(self):
        items = []  # QList<DownloadItem>
        for idx in range(self._ui.list.count()):
            downItem = self._ui.list.itemWidget(self._ui.list.item(idx))
            if not downItem:
                continue
            if downItem.isDownloading():
                continue
            items.append(downItem)
        qtUtil.qDeleteAll(items)
        self.downloadsCountChanged.emit()

    def _deleteItem(self, item):
        '''
        @parma: item DownloadItem
        '''
        if item and not item.isDownloading():
            item.deleteLater()

    def _downloadFinished(self, success):
        '''
        @param: success bool
        '''
        self._activeDownloadsCount = 0
        downloadingAllFilesFinished = True
        for idx in range(self._ui.list.count()):
            downItem = self._ui.list.itemWidget(self._ui.list.item(idx))
            if not isinstance(downItem, DownloadItem):
                continue
            if downItem.isDownloading():
                self._activeDownloadsCount += 1
            if downItem.isCancelled() or not downItem.isDownloading():
                continue
            downloadingAllFilesFinished = False

        self.downloadsCountChanged.emit()

        if downloadingAllFilesFinished:
            if success and gVar.app.activeWindow() != self:
                gVar.app.desktopNotifications().showNotification(
                    QIcon.fromTheme('download', QIcon(':/icons/other/download.svg')),
                    _('App: Download Finished'), _('All files have been successfully downloaded.'))
                if not self._closeOnFinish:
                    self.raise_()
                    self.activateWindow()
            self._ui.speedLabel.clear()
            self.setWindowTitle(_('Download Manager'))
            if const.OS_WIN:
                self.taskbarButton().progress().hide()
            if self._closeOnFinish:
                self.close()

    # Q_SIGNALS
    resized = pyqtSignal(QSize)
    downloadsCountChanged = pyqtSignal()

    # private:
    # override
    def timerEvent(self, event):
        '''
        @param: event QTimerEvent
        '''
        remTimes = []  # QVector<QTime>
        progresses = []  # QVector<int>
        speeds = []  # QVector<double>

        if event.timerId() == self._timer.timerId():
            if not self._ui.list.count():
                self._ui.speedLabel.clear()
                self.setWindowTitle(_('Download Manager'))
                if const.OS_WIN:
                    self.taskbarButton().progress().hide()
                return
            for idx in range(self._ui.list.count()):
                downItem = self._ui.list.itemWidget(self._ui.list.item(idx))
                if not isinstance(downItem, DownloadItem) or downItem.isCancelled() \
                        or not downItem.isDownloading():
                    continue
                progresses.append(downItem.progress())
                remTimes.append(downItem.remainingTime())
                speeds.append(downItem.currentSpeed())
            if not remTimes:
                return

            remaining = QTime()
            for time in remTimes:
                if time > remaining:
                    remaining = time

            progress = 0
            for prog in progresses:
                progress += prog

            progress = int(progress / len(progresses) * 100) / 100

            speed = sum(speeds)

            if not const.OS_WIN:
                self._ui.speedLabel.setText(_('%s%% of %s files (%s) %s remaining') %
                        (progress, len(progresses), DownloadItem.currentSpeedToString(speed),
                        DownloadItem.remainingTimeToString(remaining)))
            else:
                self.setWindowTitle(_('%s%% - Download Manager') % progress)
            if const.OS_WIN:
                self.taskbarButton().progress().show()
                self.taskbarButton().progress().setValue(progress)

        super().timerEvent(event)

    # override
    def closeEvent(self, event):
        '''
        @param: event QCloseEvent
        '''
        if gVar.app.windowCount() == 0:  # No main window -> we are going to quit
            if not self.canClose():
                # QMessageBox.StandardButton
                button = QMessageBox.warning(self, _('Warning'),
                    _('Are you sure you want to quit? All uncompleted downloads will be cancelled!'),
                    QMessageBox.Yes | QMessageBox.No)
                if button != QMessageBox.Yes:
                    event.ignore()
                    return
                self._isClosing = True
            gVar.app.quitApplication()
        event.accept()

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super().resizeEvent(event)
        self.resized.emit(self.size())

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        if event.key() == Qt.Key_Escape or (event.key() == Qt.Key_W and
                event.modifiers() == Qt.ControlModifier):
            self.close()

        super().keyPressEvent(event)

    def closeDownloadTab(self, item):  # noqa C901
        '''
        @param: item QWebEngineDownloadItem
        '''
        # Attemp to close empty tab that was opened only for loading the
        # download url
        def testWebView(view, url):
            '''
            @param: view TabbedWebView
            @param: url QUrl
            '''
            if not view.webTab().isRestored():
                return False
            if view.browserWindow().tabWidget().tabBar().normalTabsCount() < 2:
                return False
            page = view.page()
            if page.history().count() != 0:
                return False
            if const.QTWEBENGINEWIDGETS_VERSION >= const.QT_VERSION_CHECK(5, 12, 0):
                return True
            else:
                if page.url() != QUrl():
                    return False
                tabUrl = page.requestedUrl()
                if tabUrl.isEmpty():
                    tabUrl = QUrl(view.webTab().locationBar().text())
                return tabUrl.host() == url.host()

        if const.QTWEBENGINEWIDGETS_VERSION >= const.QT_VERSION_CHECK(5, 12, 0):
            from mc.webengine.WebPage import WebPage
            from mc.webtab.TabbedWebView import TabbedWebView
            page = item.page()
            if not page:
                return
            if not isinstance(page, WebPage):
                return
            view = page.view()
            if not isinstance(view, TabbedWebView):
                return
            if testWebView(view, QUrl()):
                view.closeView()
        else:
            mainWindow = gVar.app.getWindow()
            # If the main window was closed, threre is no need to go further
            if mainWindow == None:
                return

            if testWebView(mainWindow.weView(), item.url()):
                mainWindow.weView().closeView()
                return

            windows = gVar.app.windows()
            for window in windows:
                tabs = window.tabWidget().allTabs()
                for tab in tabs:
                    view = tab.webView()
                    if testWebView(view, item.url()):
                        view.closeView()
                        return

    def taskbarButton(self):
        '''
        @return: QWinTaskbarButton
        '''
        if const.OS_WIN:
            if not self._taskbarButton:
                window = gVar.app.getWindow()
                self._taskbarButton = QWinTaskbarButton(window and window.windowHandle() or self.windowHandle())
                self._taskbarButton.progress().setRange(0, 100)
            return self._taskbarButton
        else:
            return None
