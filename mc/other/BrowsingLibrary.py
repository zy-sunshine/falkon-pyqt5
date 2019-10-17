from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.Qt import QSize
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QIcon
from PyQt5.QtWidgets import QMenu
from mc.app.Settings import Settings
from mc.common.globalvars import gVar
from PyQt5.Qt import Qt
from mc.bookmarks.bookmarksimport.BookmarksImportDialog import BookmarksImportDialog
from mc.bookmarks.bookmarksexport.BookmarksExportDialog import BookmarksExportDialog
from mc.history.HistoryManager import HistoryManager
from mc.bookmarks.BookmarksManager import BookmarksManager
from mc.lib3rd.FancyTabWidget import FancyTabWidget

class BrowsingLibrary(QWidget):
    def __init__(self, window, parent=None):
        '''
        @param: window BrowserWindow
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/other/BrowsingLibrary.ui', self)
        self._historyManager = HistoryManager(window)  # HistoryManager
        self._bookmarksManager = BookmarksManager(window)  # BookmarksManager

        settings = Settings()
        settings.beginGroup('BrowsingLibrary')
        self.resize(settings.value('size', QSize(760, 470)))
        self._historyManager.restoreState(settings.value('historyState', QByteArray()))
        settings.endGroup()

        gVar.appTools.centerWidgetOnScreen(self)

        historyIcon = QIcon()
        historyIcon.addFile(':/icons/other/bighistory.svg', QSize(), QIcon.Normal)
        historyIcon.addFile(':/icons/other/bighistory-selected.svg', QSize(), QIcon.Selected)

        bookmarksIcon = QIcon()
        bookmarksIcon.addFile(':/icons/other/bigstar.svg', QSize(), QIcon.Normal)
        bookmarksIcon.addFile(':/icons/other/bigstar-selected.svg', QSize(), QIcon.Selected)

        self._ui.tabs.AddTab(self._historyManager, historyIcon, _('History'))
        self._ui.tabs.AddTab(self._bookmarksManager, bookmarksIcon, _('Bookmarks'))
        self._ui.tabs.SetMode(FancyTabWidget.Mode_LargeSidebar)
        self._ui.tabs.setFocus()

        m = QMenu()
        m.addAction(_('Import Bookmarks...'), self._importBookmarks)
        m.addAction(_('Export Bookmarks...'), self._exportBookmarks)
        self._ui.importExport.setMenu(m)

        self._ui.tabs.CurrentChanged.connect(self._ui.searchLine.clear)
        self._ui.searchLine.textChanged.connect(self._search)

        gVar.appTools.setWmClass('Browsing Library', self)

    def showHistory(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._ui.tabs.SetCurrentIndex(0)
        self.show()
        self._historyManager.setMainWindow(window)

        self.raise_()
        self.activateWindow()

    def showBookmarks(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._ui.tabs.SetCurrentIndex(1)
        self.show()
        self._bookmarksManager.setMainWindow(window)

        self.raise_()
        self.activateWindow()

    def historyManager(self):
        '''
        @return: HistoryManager
        '''
        return self._historyManager

    def bookmarksManager(self):
        '''
        @return: BookmarksManager
        '''
        return self._bookmarksManager

    # private Q_SLOTS:
    def _search(self):
        if self._ui.tabs.current_index() == 0:
            self._historyManager.search(self._ui.searchLine.text())
        else:
            self._bookmarksManager.search(self._ui.searchLine.text())

    def _importBookmarks(self):
        dialog = BookmarksImportDialog(self)
        dialog.open()

    def _exportBookmarks(self):
        dialog = BookmarksExportDialog(self)
        dialog.open()

    # private:
    def closeEvent(self, event):
        '''
        @param: event QCloseEvent
        '''
        settings = Settings()
        settings.beginGroup('BrowsingLibrary')
        settings.setValue('size', self.size())
        settings.setValue('historySize', self._historyManager.saveState())
        settings.endGroup()
        event.accept()

    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        evtKey = event.key()
        evtMod = event.modifiers()
        if evtKey == Qt.Key_Escape or \
                (evtKey == Qt.Key_W and evtMod == Qt.ControlModifier):
            self.close()

        super().keyPressEvent(event)
