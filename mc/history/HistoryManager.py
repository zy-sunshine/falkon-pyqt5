from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.Qt import QUrl
from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import QIcon
from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import Qt
from .HistoryTreeView import HistoryTreeView
from mc.common.globalvars import gVar
from mc.common import const
from mc.tools.IconProvider import IconProvider

class HistoryManager(QWidget):
    def __init__(self, window, parent=None):
        '''
        @param: window BrowserWindow
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/history/HistoryManager.ui', self)
        self._window = window
        self._ui.historyTree.setViewType(HistoryTreeView.HistoryManagerViewType)

        self._ui.historyTree.urlActivated.connect(self._urlActivated)
        self._ui.historyTree.urlCtrlActivated.connect(self._urlCtrlActivated)
        self._ui.historyTree.urlShiftActivated.connect(self._urlShiftActivated)
        self._ui.historyTree.contextMenuRequested.connect(self._createContextMenu)

        self._ui.deleteB.clicked.connect(self._ui.historyTree.removeSelectedItems)
        self._ui.clearAll.clicked.connect(self._clearHistory)

        self._ui.historyTree.setFocus()

    def setMainWindow(self, window):
        '''
        @param: window BrwoserWindow
        '''
        if window:
            self._window = window

    def restoreState(self, state):
        '''
        @param: state QByteArray
        '''
        self._ui.historyTree.header().restoreState(state)

    def saveState(self):
        '''
        @return: QByteArray
        '''
        return self._ui.historyTree.header().saveState()

    # public Q_SLOTS:
    def search(self, searchText):
        self._ui.historyTree.search(searchText)

    # private Q_SLOTS:
    def _urlActivated(self, url):
        self._openUrl(url)

    def _urlCtrlActivated(self, url):
        self._openUrlInNewTab(url)

    def _urlShiftActivated(self, url):
        self._openUrlInNewWindow(url)

    def _openUrl(self, url=QUrl()):
        url = not url.isEmpty() and url or self._ui.historyTree.selectedUrl()
        self._window.weView().loadByUrl(url)

    def _openUrlInNewTab(self, url=QUrl()):
        url = not url.isEmpty() and url or self._ui.historyTree.selectedUrl()
        self._window.tabWidget().addView(url, gVar.appSettings.newTabPosition)

    def _openUrlInNewWindow(self, url=QUrl()):
        url = not url.isEmpty() and url or self._ui.historyTree.selectedUrl()
        gVar.app.createWindow(const.BW_NewWindow, url)
        self._window.weView().loadByUrl(url)

    def _openUrlInNewPrivateWindow(self, url=QUrl()):
        url = not url.isEmpty() and url or self._ui.historyTree.selectedUrl()
        gVar.app.startPrivateBrowsing(url)

    def _createContextMenu(self, pos):
        menu = QMenu()
        actNewTab = menu.addAction(IconProvider.newTabIcon(), _("Open in new tab"))
        actNewWindow = menu.addAction(IconProvider.newWindowIcon(), _("Open in new window"))
        actNewPrivateWindow = menu.addAction(IconProvider.privateBrowsingIcon(), _("Open in new private window"))

        menu.addSeparator()
        actCopyUrl = menu.addAction(_("Copy url"), self._copyUrl)
        actCopyTitle = menu.addAction(_("Copy title"), self._copyTitle)

        menu.addSeparator()
        actDelete = menu.addAction(QIcon.fromTheme("edit-delete"), _("Delete"))

        actNewTab.triggered.connect(self._openUrlInNewTab)
        actNewWindow.triggered.connect(self._openUrlInNewWindow)
        actNewPrivateWindow.triggered.connect(self._openUrlInNewPrivateWindow)
        actDelete.triggered.connect(self._ui.historyTree.removeSelectedItems)

        if self._ui.historyTree.selectedUrl().isEmpty():
            actNewTab.setDisabled(True)
            actNewWindow.setDisabled(True)
            actNewPrivateWindow.setDisabled(True)
            actCopyTitle.setDisabled(True)
            actCopyUrl.setDisabled(True)

        menu.exec_(pos)

    def _copyUrl(self):
        urlStr = self._ui.historyTree.selectedUrl().toString()
        QApplication.clipboard().setText(urlStr)

    def _copyTitle(self):
        title = self._ui.historyTree.currentIndex().data().toString()
        QApplication.clipboard().setText(title)

    def _clearHistory(self):
        button = QMessageBox.warning(self, _('Confirmation'),
            _('Are you sure you want to delete all history?'),
            QMessageBox.Yes | QMessageBox.No)
        if button != QMessageBox.Yes:
            return

        gVar.app.history().clearHistory()

    # private
    # override
    def keyPressEvent(self, event):
        '''
        @param: QKeyEvent
        '''
        if event.key() == Qt.Key_Delete:
            self._ui.historyTree.removeSelectedItem()

        super().keyPressEvent(event)

    def _getWindow(self):
        '''
        @param: return BrowserWindow
        '''
        if not self._window:
            self._window = gVar.app.getWindow()
        return self._window
