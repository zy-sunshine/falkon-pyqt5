from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import Qt
from PyQt5.Qt import QTreeWidgetItem
from PyQt5.Qt import QFileInfo
from PyQt5.Qt import QPalette
from mc.common.globalvars import gVar

class SessionManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._ui = uic.loadUi('mc/session/SessionManagerDialog.ui', self)
        #self._ui.treeWidget.setItemDelegate(RemoveItemFocusDelegate(self._ui.treeWidget))

        self._ui.newButton.clicked.connect(self._newSession)
        self._ui.renameButton.clicked.connect(self._renameSession)
        self._ui.cloneButton.clicked.connect(self._cloneSession)
        self._ui.deleteButton.clicked.connect(self._deleteSession)
        self._ui.switchToButton.clicked.connect(self._switchToSession)
        self._ui.treeWidget.currentItemChanged.connect(self._updateButtons)

        self._refresh()
        gVar.app.sessionManager().sessionsMetaDataChanged.connect(self._refresh)

    # private
    # enum Roles
    _SessionFileRole = Qt.UserRole + 10
    _IsBackupSessionRole = Qt.UserRole + 11
    _IsActiveSessionRole = Qt.UserRole + 12
    _IsDefaultSessionRole = Qt.UserRole + 13

    def _newSession(self):
        gVar.app.sessionManager()._newSession()

    def _renameSession(self):
        item = self._ui.treeWidget.currentItem()
        if not item:
            return
        filePath = item.data(0, self._SessionFileRole)
        if filePath:
            gVar.app.sessionManager()._renameSession(filePath)

    def _cloneSession(self):
        item = self._ui.treeWidget.currentItem()
        if not item:
            return
        filePath = item.data(0, self._SessionFileRole)
        if filePath:
            gVar.app.sessionManager()._cloneSession(filePath)

    def _deleteSession(self):
        item = self._ui.treeWidget.currentItem()
        if not item:
            return
        filePath = item.data(0, self._SessionFileRole)
        if filePath:
            gVar.app.sessionManager()._deleteSession(filePath)

    def _switchToSession(self):
        item = self._ui.treeWidget.currentItem()
        if not item:
            return
        filePath = item.data(0, self._SessionFileRole)
        if filePath:
            isBackupSession = item.data(0, self._IsBackupSessionRole)
            if isBackupSession:
                gVar.app.sessionManager()._replaceSession(filePath)
            else:
                gVar.app.sessionManager()._switchSession(filePath)

    def _refresh(self):
        self._ui.treeWidget.clear()

        sessions = gVar.app.sessionManager()._sessionMetaData()
        for session in sessions:
            item = QTreeWidgetItem()
            item.setText(0, session.name)
            item.setText(1, QFileInfo(session.filePath).lastModified().toString(Qt.DefaultLocaleShortDate))
            item.setData(0, self._SessionFileRole, session.filePath)
            item.setData(0, self._IsBackupSessionRole, session.isBackup)
            item.setData(0, self._IsActiveSessionRole, session.isActive)
            item.setData(0, self._IsDefaultSessionRole, session.isDefault)
            self._updateItem(item)
            self._ui.treeWidget.addTopLevelItem(item)

        self._updateButtons()

    def _updateButtons(self):
        # QTreeWidgetItem
        item = self._ui.treeWidget.currentItem()
        isBackup = bool(item and item.data(0, self._IsBackupSessionRole))
        isActive = bool(item and item.data(0, self._IsActiveSessionRole))
        isDefault = bool(item and item.data(0, self._IsDefaultSessionRole))

        self._ui.renameButton.setEnabled(bool(item and not isDefault and not isBackup))
        self._ui.cloneButton.setEnabled(bool(item and not isBackup))
        self._ui.deleteButton.setEnabled(bool(item and not isBackup and not isDefault and not isActive))
        self._ui.switchToButton.setEnabled(bool(item and not isActive))
        self._ui.switchToButton.setText(isBackup and _('Restore') or _('Switch To'))

    def _updateItem(self, item):
        '''
        @param: item QTreeWidgetItem
        '''
        isBackup = bool(item and item.data(0, self._IsBackupSessionRole))
        isActive = bool(item and item.data(0, self._IsActiveSessionRole))
        isDefault = bool(item and item.data(0, self._IsDefaultSessionRole))

        # QFont
        font = item.font(0)

        if isBackup:
            color = self.palette().color(QPalette.Disabled, QPalette.WindowText)
            item.setForeground(0, color)
            item.setForeground(1, color)

        if isActive:
            font.setBold(True)
            item.setFont(0, font)
            item.setFont(1, font)

        if isDefault:
            font.setItalic(True)
            item.setFont(0, font)
            item.setFont(1, font)

    # override
    def showEvent(self, event):
        super().showEvent(event)
        self._resizeViewHeader()

    # override
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resizeViewHeader()

    def _resizeViewHeader(self):
        headerWidth = self._ui.treeWidget.header().width()
        self._ui.treeWidget.header().resizeSection(0, headerWidth - headerWidth / 2.5)
