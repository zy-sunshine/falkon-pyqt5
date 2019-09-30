from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox
from mc.common import const
from mc.common.globalvars import gVar
from mc.bookmarks.BookmarksModel import BookmarksModel
from mc.bookmarks.BookmarksItemDelegate import BookmarksItemDelegate
from .ChromeImporter import ChromeImporter
from .FirefoxImporter import FirefoxImporter
from .HtmlImporter import HtmlImporter
from .IeImporter import IeImporter
from .OperaImporter import OperaImporter

class BookmarksImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentPage = 0
        self._importer = None  # BookmarksImporter
        self._importedFolder = None  # BookmarkItem
        self._model = None  # BookmarksModel

        self.setAttribute(Qt.WA_DeleteOnClose)
        self._ui = uic.loadUi('mc/bookmarks/bookmarksimport/BookmarksImportDialog.ui', self)

        self._ui.browserList.setCurrentRow(0)
        self._ui.treeView.setItemDelegate(BookmarksItemDelegate(self._ui.treeView))

        self._ui.nextButton.clicked.connect(self._nextPage)
        self._ui.backButton.clicked.connect(self._previousPage)
        self._ui.chooseFile.clicked.connect(self._setFile)
        self._ui.cancelButton.clicked.connect(self.close)

        if not const.OS_WIN:
            self._ui.browserList.setItemHidden(self._ui.browserList.item(self._IE), True)

    # private Q_SLOTS:
    def _nextPage(self):  # noqa C901
        if self._currentPage == 0:
            if not self._ui.browserList.currentItem():
                return
            row = self._ui.browserList.currentRow()
            if row == self._Firefox:
                self._importer = FirefoxImporter()
            elif row == self._Chrome:
                self._importer = ChromeImporter()
            elif row == self._Opera:
                self._importer = OperaImporter()
            elif row == self._IE:
                self._importer = IeImporter()
            elif row == self._Html:
                self._importer = HtmlImporter()

            self._ui.fileLine.clear()
            self._showImporterPage()

            self._ui.nextButton.setEnabled(False)
            self._ui.backButton.setEnabled(True)
            self._currentPage += 1
            self._ui.stackedWidget.setCurrentIndex(self._currentPage)
        elif self._currentPage == 1:
            if not self._ui.fileLine.text():
                return

            if self._importer.prepareImport():
                self._importedFolder = self._importer.importBookmarks()

            if self._importer.error():
                QMessageBox.critical(self, _('Error!'), self._importer.errorString())
                return

            if not self._importedFolder or not self._importedFolder.children():
                QMessageBox.warning(self, _('Error!'), _('No bookmarks were found.'))
                return

            assert(self._importedFolder.isFolder())

            self._currentPage += 1
            self._ui.stackedWidget.setCurrentIndex(self._currentPage)
            self._ui.nextButton.setText(_('Finish'))
            self._showExportedBookmarks()
        elif self._currentPage == 2:
            self._addExportedBookmarks()
            self.close()
        else:
            raise RuntimeError('Unreachable')

    def _previousPage(self):
        if self._currentPage == 0:
            pass
        elif self._currentPage == 1:
            self._ui.nextButton.setEnabled(True)
            self._ui.backButton.setEnabled(False)
            self._currentPage -= 1
            self._ui.stackedWidget.setCurrentIndex(self._currentPage)

            self._importer = None
        elif self._currentPage == 2:
            self._showImporterPage()

            self._ui.nextButton.setText(_('Next >'))
            self._ui.nextButton.setEnabled(True)
            self._ui.backButton.setEnabled(True)
            self._currentPage -= 1
            self._ui.stackedWidget.setCurrentIndex(self._currentPage)

            self._ui.treeView.setModel(None)
            self._model = None

            self._importedFolder = None
        else:
            raise RuntimeError('Unreachable')

    def _setFile(self):
        assert(self._importer)

        fpath = self._importer.getPath(self)
        self._ui.fileLine.setText(fpath)
        self._ui.nextButton.setEnabled(bool(self._ui.fileLine.text()))

    # private:
    # enum Browser
    _Firefox = 0
    _Chrome = 1
    _Opera = 2
    _IE = 3
    _Html = 4

    def _showImporterPage(self):
        self._ui.iconLabel.setPixmap(self._ui.browserList.currentItem().icon().pixmap(48))
        self._ui.importingFromLabel.setText(_('<b>Importing from %s</b>') %
                self._ui.browserList.currentItem().text())
        self._ui.fileText1.setText(self._importer.description())
        self._ui.standardDirLabel.setText('<i>%s</i>' % self._importer.standardPath())

    def _showExportedBookmarks(self):
        self._model = BookmarksModel(self._importedFolder, None, self)
        self._ui.treeView.setModel(self._model)
        self._ui.treeView.header().resizeSection(0, self._ui.treeView.header().width() / 2)
        self._ui.treeView.expandAll()

    def _addExportedBookmarks(self):
        gVar.app.bookmarks().addBookmark(gVar.app.bookmarks().unsortedFolder(), self._importedFolder)
        self._importedFolder = None
