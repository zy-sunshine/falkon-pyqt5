import re
from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.Qt import QGuiApplication
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTableWidgetItem
from mc.common.globalvars import gVar
from mc.common import const
from mc.app.Settings import Settings

class UserAgentDialog(QDialog):
    def __init__(self, parent=None):
        '''
        @param parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/preferences/UserAgentDialog.ui', self)
        self._manager = gVar.app.userAgentManager()  # UserAgentManager

        self._knownUserAgents = []  # QStringList

        self.setAttribute(Qt.WA_DeleteOnClose)

        self._ui.globalComboBox.setLayoutDirection(Qt.LeftToRight)
        self._ui.table.setLayoutDirection(Qt.LeftToRight)

        # QString
        os = gVar.appTools.operatingSystemLong()

        if const.OS_UNIX:
            if QGuiApplication.platformName() == 'xcb':
                os += 'X11; '
            elif QGuiApplication.platformName() == 'wayland':
                os += 'Wayland; '
        chromeRx = re.compile(r'Chrome/([^\s]+)')
        dUserAgent = self._manager.defaultUserAgent()
        chromeVersion = chromeRx.search(dUserAgent).groups()[0]

        self._knownUserAgents.extend([
            "Opera/9.80 (%s) Presto/2.12.388 Version/12.16" % os,
            "Mozilla/5.0 (%s) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s Safari/537.36" % (os, chromeVersion),
            "Mozilla/5.0 (%s) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12" % os,
            "Mozilla/5.0 (%s; rv:57.0) Gecko/20100101 Firefox/57.0" % os,
        ])

        self._ui.globalComboBox.addItems(self._knownUserAgents)

        # QString
        globalUserAgent = self._manager.globalUserAgent()
        self._ui.changeGlobal.setChecked(bool(globalUserAgent))
        self._ui.globalComboBox.lineEdit().setText(globalUserAgent)
        self._ui.globalComboBox.lineEdit().setCursorPosition(0)

        self._ui.changePerSite.setChecked(self._manager.usePerDomainUserAgents())

        for siteItem, userAgentItem in self._manager.perDomainUserAgentsList():
            row = self._ui.table.rowCount()

            self._ui.table.insertRow(row)
            self._ui.table.setItem(row, 0, siteItem)
            self._ui.table.setItem(row, 1, userAgentItem)

        self._ui.table.sortByColumn(-1, Qt.AscendingOrder)

        self._ui.add.clicked.connect(self._addSite)
        self._ui.remove.clicked.connect(self._removeSite)
        self._ui.edit.clicked.connect(self._editSite)
        self._ui.table.clicked.connect(self._editSite)

        self._ui.changeGlobal.clicked.connect(self._enableGlobalComboBox)
        self._ui.changePerSite.clicked.connect(self._enablePerSiteFrame)

        self._enableGlobalComboBox(self._ui.changeGlobal.isChecked())
        self._enablePerSiteFrame(self._ui.changePerSite.isChecked())

    # private Q_SLOTS:
    def _addSite(self):
        site = ''
        userAgent = ''

        ok, site, userAgent = self._showEditDialog(_('Add new site'))
        if ok:
            siteItem = QTableWidgetItem(site)
            userAgentItem = QTableWidgetItem(userAgent)

            row = self._ui.table.rowCount()

            self._ui.table.insertRow(row)
            self._ui.table.setItem(row, 0, siteItem)
            self._ui.table.setItem(row, 1, userAgentItem)

    def _removeSite(self):
        row = self._ui.table.currentRow()

        siteItem = self._ui.table.item(row, 0)
        userAgentItem = self._ui.table.item(row, 1)

        if siteItem and userAgentItem:
            self._ui.table.removeRow(row)

    def _editSite(self):
        row = self._ui.table.currentRow()

        siteItem = self._ui.table.item(row, 0)
        userAgentItem = self._ui.table.item(row, 1)

        if siteItem and userAgentItem:
            site = siteItem.text()
            userAgent = userAgentItem.text()

            ok, site, userAgent = self._showEditDialog(_('Edit site'), site, userAgent)
            if ok:
                siteItem.setText(site)
                userAgentItem.setText(userAgent)

    # override
    def accept(self):
        if self._ui.changeGlobal.isChecked():
            globalUserAgent = self._ui.globalComboBox.currentText()
        else:
            globalUserAgent = ''

        domainList = []
        userAgentsList = []

        for idx in range(self._ui.table.rowCount()):
            siteItem = self._ui.table.item(idx, 0)
            userAgentItem = self._ui.table.item(idx, 1)

            if not siteItem or not userAgentItem:
                continue

            domain = siteItem.text().strip()
            userAgent = userAgentItem.text().strip()

            if not domain or not userAgent:
                continue

            domainList.append(domain)
            userAgentsList.append(userAgent)

        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        settings.setValue('UserAgent', globalUserAgent)
        settings.endGroup()

        settings.beginGroup('User-Agent-Settings')
        settings.setValue('UsePerDomainUA', self._ui.changePerSite.isChecked())
        settings.setValue('DomainList', domainList)
        settings.setValue('UserAgentsList', userAgentsList)
        settings.endGroup()

        self._manager.loadSettings()
        gVar.app.networkManager().loadSettings()
        self.close()

    def _enableGlobalComboBox(self, enable):
        '''
        @param: enable bool
        '''
        self._ui.globalComboBox.setEnabled(enable)

    def _enablePerSiteFrame(self, enable):
        self._ui.perSiteFrame.setEnabled(enable)

    # private:
    def _showEditDialog(self, title, rSite='', rUserAgent=''):
        if not rSite or not rUserAgent:
            return False, '', ''

        dialog = QDialog(self)
        layout = QFormLayout(dialog)
        editSite = QLineEdit(dialog)
        editAgent = QComboBox(dialog)
        editAgent.setLayoutDirection(Qt.LeftToRight)
        editAgent.setEditable(True)
        editAgent.addItems(self._knownUserAgents)

        box = QDialogButtonBox(dialog)
        box.addButton(QDialogButtonBox.Ok)
        box.addButton(QDialogButtonBox.Cancel)

        box.rejected.connect(dialog.reject)
        box.accepted.connect(dialog.accept)

        layout.addRow(QLabel(_('Site domain:')), editSite)
        layout.addRow(QLabel(_('User Agent:')), editAgent)
        layout.addRow(box)

        editSite.setText(rSite)
        editAgent.lineEdit().setText(rUserAgent)

        editSite.setFocus()
        editAgent.lineEdit().setCursorPosition(0)

        dialog.setWindowTitle(title)
        dialog.setMinimumSize(550, 100)
        dialog.setMaximumWidth(550)

        if dialog.exec_():
            rSite = editSite.text()
            rUserAgent = editAgent.currentText()

            return bool(rSite and rUserAgent)

        return False
