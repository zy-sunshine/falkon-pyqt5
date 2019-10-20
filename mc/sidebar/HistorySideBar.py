from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QUrl
from PyQt5 import uic
from mc.common.globalvars import gVar
from mc.common import const
from PyQt5.QtWidgets import QMenu
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QIcon
from mc.history.HistoryTreeView import HistoryTreeView

class HistorySideBar(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('mc/sidebar/HistorySideBar.ui', self)
        self._window = window

        self.ui.historyTree.setViewType(HistoryTreeView.HistorySidebarViewType)

        self.ui.historyTree.urlActivated.connect(self._urlActivated)
        self.ui.historyTree.urlCtrlActivated.connect(self._urlCtrlActivated)
        self.ui.historyTree.urlShiftActivated.connect(self._urlShiftActivated)
        self.ui.historyTree.contextMenuRequested.connect(self._createContextMenu)

    # private Q_SLOTS:
    def _urlActivated(self, url):
        self._openUrl(url)

    def _urlCtrlActivated(self, url):
        self._openUrlInNewTab(url)

    def _urlShiftActivated(self, url):
        self._openUrlInNewWindow(url)

    def _openUrl(self, url=QUrl()):
        if url.isEmpty():
            url = self.ui.historyTree.selectedUrl()
        self._window.weView().loadByUrl(url)

    def _openUrlInNewTab(self, url=QUrl()):
        if url.isEmpty():
            url = self.ui.historyTree.selectedUrl()
        self._window.tabWidget().addViewByUrl(url, gVar.appSettings.newTabPosition)

    def _openUrlInNewWindow(self, url=QUrl()):
        if url.isEmpty():
            url = self.ui.historyTree.selectedUrl()
        gVar.app.createWindow(const.BW_NewWindow, url)

    def _openUrlInNewPrivateWindow(self, url=QUrl()):
        if url.isEmpty():
            url = self.ui.historyTree.selectedUrl()
        gVar.app.startPrivateBrowsing(url)

    def _createContextMenu(self, pos):
        '''
        @param: pos QPoint
        '''
        menu = QMenu()
        actNewTab = menu.addAction(IconProvider.newTabIcon(), _('Open in new tab'))
        actNewWindow = menu.addAction(IconProvider.newWindowIcon(), _('Open in new window'))
        actNewPrivateWindow = menu.addAction(IconProvider.privateBrowsingIcon(), _('Open in new private window'))

        menu.addSeparator()
        actDelete = menu.addAction(QIcon.fromTheme('edit-delete'), _('Delete'))

        actNewTab.triggered.connect(lambda x: self._openUrlInNewTab())
        actNewWindow.triggered.connect(lambda x: self._openUrlInNewWindow())
        actNewPrivateWindow.triggered.connect(lambda x: self._openUrlInNewPrivateWindow())
        actDelete.triggered.connect(self.ui.historyTree.removeSelectedItems)

        if self.ui.historyTree.selectedUrl().isEmpty():
            actNewTab.setDisabled(True)
            actNewWindow.setDisabled(True)
            actNewPrivateWindow.setDisabled(True)

        menu.exec_(pos)
