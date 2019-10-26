from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import Qt
from PyQt5.Qt import QTreeWidgetItem
from mc.common.globalvars import gVar

class ProtocolHandlerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/other/ProtocolHandlerDialog.ui', self)

        self.setAttribute(Qt.WA_DeleteOnClose)

        self._init()

        self._ui.treeWidget.header().resizeSection(0, 100)
        self._ui.remove.clicked.connect(self._removeEntry)
        self._ui.buttonBox.accepted.connect(self._accepted)
        self._ui.buttonBox.rejected.connect(self.close)

    # private:
    def _init(self):
        handlers = gVar.app.protocolHandlerManager().protocolHandlers()

        for name, handler in handlers.items():
            item = QTreeWidgetItem(self._ui.treeWidget)
            item.setText(0, name)
            item.setText(1, handler.host())
            self._ui.treeWidget.addTopLevelItem(item)

    def _accepted(self):
        pMgr = gVar.app.protocolHandlerManager()
        handlers = pMgr.protocolHandlers()

        for idx in range(self._ui.treeWidget.topLevelItemCount()):
            item = self._ui.treeWidget.topLevelItem(idx)
            handlers.pop(item.text(0))

        for key, handler in handlers.items():
            pMgr.removeProtocolHandler(key)

        self.close()

    def _removeEntry(self):
        item = self._ui.treeWidget.currentItem()
        if not item:
            return
        (item.parent() or self._ui.treeWidget.invisibleRootItem()).removeChild(item)
