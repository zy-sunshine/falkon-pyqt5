from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.Qt import QShortcut
from PyQt5.Qt import QKeySequence
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QInputDialog
from PyQt5.Qt import QDateTime
from PyQt5.Qt import QStyle
from PyQt5.Qt import QNetworkCookie
from PyQt5.QtWidgets import QTreeWidgetItem
from mc.common.globalvars import gVar
from mc.app.Settings import Settings
from mc.common import const
from mc.tools.TreeWidget import TreeWidget
from mc.tools.IconProvider import IconProvider

class CookieManager(QDialog):
    def __init__(self, parent=None):
        '''
        @param parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/cookies/CookieManager.ui', self)

        self._domainHash = {}  # QHash<QString, QTreeWidgetItem>
        self._itemHash = {}  # QHash<QTreeWidgetItem, QNetworkCookie>

        self.setAttribute(Qt.WA_DeleteOnClose)

        gVar.appTools.centerWidgetOnScreen(self)

        if self.isRightToLeft():
            self._ui.cookieTree.headerItem().setTextAlignment(0, Qt.AlignRight | Qt.AlignVCenter)
            self._ui.cookieTree.headerItem().setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
            self._ui.cookieTree.setLayoutDirection(Qt.LeftToRight)
            self._ui.whiteList.setLayoutDirection(Qt.LeftToRight)
            self._ui.blackList.setLayoutDirection(Qt.LeftToRight)

        # Stored Cookies
        self._ui.cookieTree.currentItemChanged.connect(self._currentItemChanged)
        self._ui.removeAll.clicked.connect(self._removeAll)
        self._ui.removeOne.clicked.connect(self._remove)
        self._ui.close.clicked.connect(lambda: self.close())
        self._ui.close2.clicked.connect(lambda: self.close())
        self._ui.close3.clicked.connect(lambda: self.close())
        self._ui.search.textChanged.connect(self._filterString)

        # Cookie Filtering
        self._ui.whiteAdd.clicked.connect(self._addWhitelist)
        self._ui.whiteRemove.clicked.connect(self._removeWhitelist)
        self._ui.blackAdd.clicked.connect(self._addBlacklist)
        self._ui.blackRemove.clicked.connect(self._removeBlacklist)

        # Cookie Settings
        settings = Settings()
        settings.beginGroup('Cookie-Settings')
        self._ui.saveCookies.setChecked(settings.value('allCookies', True))
        self._ui.filter3rdParty.setChecked(settings.value('filterThirdPartyCookies', False))
        self._ui.filterTracking.setChecked(settings.value('filterTrackingCookie', False))
        self._ui.deleteCookiesOnClose.setChecked(settings.value('deleteCookiesOnClose', False))
        self._ui.whiteList.addItems(settings.value('whitelist', []))
        self._ui.blackList.addItems(settings.value('blacklist', []))
        settings.endGroup()

        if const.QTWEBENGINEWIDGETS_VERSION < const.QT_VERSION_CHECK(5, 11, 0):
            self._ui.filter3rdParty.hide()

        self._ui.search.setPlaceholderText(_('Search'))
        self._ui.cookieTree.setDefaultItemShowMode(TreeWidget.ItemsCollapsed)
        self._ui.cookieTree.sortItems(0, Qt.AscendingOrder)
        self._ui.cookieTree.header().setDefaultSectionSize(220)
        self._ui.cookieTree.setFocus()

        self._ui.whiteList.setSortingEnabled(True)
        self._ui.blackList.setSortingEnabled(True)

        self._removeShortcut = QShortcut(QKeySequence('Del'), self)
        self._removeShortcut.activated.connect(self._deletePressed)

        self._ui.search.textChanged.connect(self._filterString)
        cookieJar = gVar.app.cookieJar()
        cookieJar.cookieAdded.connect(self._addCookie)
        cookieJar.cookieRemoved.connect(self._removeCookie)

        # Load cookies
        for cookie in cookieJar.getAllCookies():
            self._addCookie(cookie)

        gVar.appTools.setWmClass('Cookies', self)

    # private Q_SLOTS:
    def _currentItemChanged(self, current, parent):
        '''
        @param: current QTreeWidgetItem
        @param: parent QTreeWidgetItem
        '''
        if not current:
            return

        if not current.text(1):
            self._ui.name.setText(_('<cookie not selected>'))
            self._ui.value.setText(_("<cookie not selected>"))
            self._ui.server.setText(_("<cookie not selected>"))
            self._ui.path.setText(_("<cookie not selected>"))
            self._ui.secure.setText(_("<cookie not selected>"))
            self._ui.expiration.setText(_("<cookie not selected>"))

            self._ui.removeOne.setText(_("Remove cookies"))
            return

        cookie = current.data(0, Qt.UserRole + 10)
        self._ui.name.setText(cookie.name().data().decode())
        self._ui.value.setText(cookie.value())
        self._ui.server.setText(self.domain())
        self._ui.path.setText(self.path())
        if cookie.isSecure():
            self._ui.secure.setText(_('Secure only'))
        else:
            self._ui.secure.setText(_('All connections'))
        if cookie.isSessionCookie():
            self._ui.expiration.setText(_('Session cookie'))
        else:
            self._ui.expiration.setText(
                QDateTime(cookie.expirationDate()).toString('hh:mm:ss dddd d. MMMM yyyy')
            )

        self._ui.removeOne.setText(_('Remove cookie'))

    def _remove(self):
        current = self._ui.cookieTree.currentItem()
        if not current:
            return

        cookies = []  # QList<QNetworkCookie>

        if current.childCount():
            for idx in range(current.childCount()):
                # QTreeWidgetItem
                item = current.child(idx)
                if item and item in self._itemHash:
                    cookies.append(self._itemHash[item])
        elif current in self._itemHash:
            cookies.append(self._itemHash[current])

        cookieJar = gVar.app.cookieJar()
        for cookie in cookies:
            cookieJar.deleteCookie(cookie)

    def _removeAll(self):
        button = QMessageBox.warning(self, _('Confirmation'),
            _('Are you sure you want to delete all cookies on your computer?'),
            QMessageBox.Yes | QMessageBox.No)

        if button != QMessageBox.Yes:
            return

        gVar.app.cookieJar().deleteAllCookies()

        self._itemHash.clear()
        self._domainHash.clear()
        self._ui.cookieTree.clear()

    def _addWhitelist(self):
        server = QInputDialog.getText(self, _('Add to whitelist'),
                _('Server:'))
        if not server:
            return

        if self._ui.blackList.findItems(server, Qt.MatchFixedString):
            QMessageBox.information(self, _('Already blacklisted!'),
                _("The server \"%s\" is already in blacklist, please remove it first.") % server)
            return

        if not self._ui.whiteList.findItems(server, Qt.MatchFixedString):
            self._ui.whiteList.addItem(server)

    def _removeWhitelist(self):
        self._ui.whiteList.currentItem().deleteLater()

    def _addBlacklist(self):
        server = QInputDialog.getText(self, _('Add to blacklist'),
                _('Server:'))
        self._addBlacklistByServer(server)

    def _removeBlacklist(self):
        self._ui.blackList.currentItem().deleteLater()

    def _deletePressed(self):
        if self._ui.cookieTree.hasFocus():
            self.remove()
        elif self._ui.whiteList.hasFocus():
            self._removeWhitelist()
        elif self._ui.blackList.hasFocus():
            self._removeBlacklist()

    def _filterString(self, string):
        '''
        @param: string QString
        '''
        if not string:
            for idx in range(self._ui.cookieTree.topLevelItemCount()):
                item = self._ui.cookieTree.topLevelItem(idx)
                item.setHidden(True)
                item.setExpanded(self._ui.cookieTree.defaultItemShowMode() == TreeWidget.ItemsExpanded)
        else:
            strLower = string.lower()
            for idx in range(self._ui.cookieTree.topLevelItemCount()):
                item = self._ui.cookieTree.topLevelItem(idx)
                text = '.' + item.text(0)
                item.setHidden(text.lower() not in strLower)
                item.setExpanded(True)

    def _addCookie(self, cookie):
        '''
        @param: cookie QNetworkCookie
        '''
        item = None  # QTreeWidgetItem
        domain = self._cookieDomain(cookie)

        findParent = self._domainHash.get(domain)
        if findParent:
            item = QTreeWidgetItem(findParent)
        else:
            newParent = QTreeWidgetItem(self._ui.cookieTree)
            newParent.setText(0, domain)
            newParent.setIcon(0, IconProvider.standardIcon(QStyle.SP_DirIcon))
            newParent.setData(0, Qt.UserRole + 10, cookie.domain())
            self._ui.cookieTree.addTopLevelItem(newParent)
            self._domainHash[domain] = newParent

            item = QTreeWidgetItem(newParent)

        cookie = QNetworkCookie(cookie)
        item.setText(0, '.' + domain)
        item.setText(1, cookie.name().data().decode())
        item.setData(0, Qt.UserRole + 10, cookie)
        self._ui.cookieTree.addTopLevelItem(item)

        import ipdb; ipdb.set_trace()
        self._itemHash[item] = cookie

    def _removeCookie(self, cookie):
        '''
        @param: cookie QNetworkCookie
        '''
        # QTreeWidgetItem
        item = self._cookieItem(cookie)
        if not item:
            return

        self._itemHash.pop(item, None)

        if item.parent() and item.parent().childCount() == 1:
            self._domainHash.pop(self._cookieDomain(cookie), None)
            item.parent().deleteLater()
            item = None

        if item:
            item.deleteLater()

    # private:
    # override
    def closeEvent(self, event):
        '''
        @param event QCloseEvent
        '''
        whitelist = []
        blacklist = []

        for idx in range(self._ui.whiteList.count()):
            item = self._ui.whiteList.item(idx)
            whitelist.append(item.text())

        for idx in range(self._ui.blacklist.count()):
            item = self._ui.blackList.item(idx)
            blacklist.append(item.text())

        settings = Settings()
        settings.beginGroup('Cookie-Settings')
        settings.setValue('allowCookies', self._ui.saveCookies.isChecked())
        settings.setValue('filterThirdPartyCookies', self._ui.filter3rdParty.isChecked())
        settings.setValue('filterTrackingCookie', self._ui.filterTracking.isChecked())
        settings.setValue('deleteCookiesOnClose', self._ui.deleteCookiesOnClose.isChecked())
        settings.setValue('whitelist', whitelist)
        settings.setValue('blacklist', blacklist)
        settings.endGroup()

        gVar.app.cookieJar().loadSettings()

        event.accept()

    # override
    def keyPressEvent(self, event):
        '''
        @param event QKeyEvent
        '''
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)

    def _addBlacklistByServer(self, server):
        '''
        @param: server QString
        '''
        if not server:
            return

        if self._ui.whiteList.findItems(server, Qt.MatchFixedString):
            QMessageBox.information(self, _('Already whitelisted!'),
                _("The server \"%s\" is already in whitelist, please remove it first.") % server)
            return

        if not self._ui.blackList.findItems(server, Qt.MatchFixedString):
            self._ui.blackList.addItem(server)

    def _cookieDomain(self, cookie):
        '''
        @param: cookie QNetworkCookie
        @return: QString
        '''
        domain = cookie.domain()
        domain = domain.lstrip('.')
        return domain

    def _cookieItem(self, cookie):
        '''
        @param: cookie QNetworkCookie
        @return: QTreeWidgetItem
        '''
        for key, val in self._itemHash.items():
            if val == cookie:
                return key
        return None
