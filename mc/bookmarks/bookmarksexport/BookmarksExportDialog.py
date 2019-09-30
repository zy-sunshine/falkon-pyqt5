from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.Qt import Qt
from mc.common.globalvars import gVar
from PyQt5.QtWidgets import QMessageBox
from .HtmlExporter import HtmlExporter

class BookmarksExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/bookmarks/bookmarksexport/BookmarksExportDialog.ui', self)
        self._exporters = []  # QList<BookmarksExporter>
        self._currentExporter = None

        self.setAttribute(Qt.WA_DeleteOnClose)
        self._init()

        self._ui.chooseOutput.clicked.connect(self._setPath)
        self._ui.buttonBox.accepted.connect(self._exportBookmarks)
        self._ui.buttonBox.rejected.connect(self.close)

    # private Q_SLOTS:
    def _setPath(self):
        assert(self._currentExporter)

        self._ui.output.setText(self._currentExporter.getPath(self))

    def _exportBookmarks(self):
        assert(self._currentExporter)

        if not self._ui.output.text():
            return

        ok = self._currentExporter.exportBookmarks(gVar.app.bookmarks().rootItem())

        if not ok:
            QMessageBox.critical(self, _('Error!'), self._currentExporter.errorString())
        else:
            self.close()

    # private:
    def _init(self):
        self._exporters.append(HtmlExporter(self))
        for exporter in self._exporters:
            self._ui.format.addItem(exporter.name())
        self._currentExporter = self._exporters[0]
