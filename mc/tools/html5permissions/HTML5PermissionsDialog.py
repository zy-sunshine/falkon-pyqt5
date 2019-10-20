from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import QTreeWidgetItem
from PyQt5.Qt import Qt
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.app.Settings import Settings
from mc.common.globalvars import gVar
from .HTML5PermissionsManager import HTML5PermissionsManager

class HTML5PermissionsDialog(QDialog):
    def __init__(self, parent=None):
        '''
        @param parent QWidget
        '''
        super().__init__(parent)

        self._ui = uic.loadUi('mc/tools/html5permissions/HTML5PermissionsDialog.ui', self)
        self._granted = {}  # QHash<QWebEnginePage::Feature, QStringList>
        self._denied = {}  # QHash<QWebEnginePage::Feature, QStringList>

        self._loadSettings()

        self._ui.treeWidget.header().resizeSection(0, 220)

        self._ui.remove.clicked.connect(self._removeEntry)
        self._ui.feature.currentIndexChanged.connect(self._featureIndexChanged)
        self._ui.buttonBox.accepted.connect(self._saveSettings)

        self.showFeaturePermissions(self._currentFeature())

    def showFeaturePermissions(self, feature):
        '''
        @param feature QWebEnginePage::Feature
        '''
        if feature not in self._granted or feature not in self._denied:
            return

        self._ui.treeWidget.clear()

        for site in self._granted[feature]:
            item = QTreeWidgetItem(self._ui.treeWidget)
            item.setText(0, site)
            item.setText(1, _('Allow'))
            item.setData(0, Qt.UserRole + 10, self.Allow)
            self._ui.treeWidget.addTopLevelItem(item)

        for site in self._denied[feature]:
            item = QTreeWidgetItem(self._ui.treeWidget)
            item.setText(0, site)
            item.setText(1, _('Deny'))
            item.setData(0, Qt.UserRole + 10, self.Deny)
            self._ui.treeWidget.addTopLevelItem(item)

    # private Q_SLOTS:
    def _removeEntry(self):
        item = self._ui.treeWidget.currentItem()
        if not item:
            return

        role = item.data(0, Qt.UserRole + 10)
        assert(type(role) is int)
        origin = item.text(0)

        if role == self.Allow:
            self._granted[self._currentFeature()].remove(origin)
        else:
            self._denied[self._currentFeature()].remove(origin)

        (item.parent() or self._ui.treeWidget.invisibleRootItem()).removeChild(item)

    def _featureIndexChanged(self):
        self.showFeaturePermissions(self._currentFeature())

    def _saveSettings(self):
        settings = Settings()
        settings.beginGroup('HTML5Notifications')
        for enumType, name in HTML5PermissionsManager.s_settingList:
            grantedName = '%sGranted' % name
            deniedName = '%sDenied' % name
            settings.setValue(grantedName, self._granted[enumType])
            settings.setValue(deniedName, self._denied[enumType])
        settings.endGroup()

        gVar.app.html5PermissionsManager().loadSettings()

    # private:
    # enum Role
    Allow = 0
    Deny = 1

    def _loadSettings(self):
        settings = Settings()
        settings.beginGroup('HTML5Notifications')
        for enumType, name in HTML5PermissionsManager.s_settingList:
            grantedName = '%sGranted' % name
            deniedName = '%sDenied' % name
            self._granted[enumType] = settings.value(grantedName, [])
            self._denied[enumType] = settings.value(deniedName, [])
        settings.endGroup()

    def _currentFeature(self):
        '''
        @return: QWebEnginePage::Feature
        '''
        index = self._ui.feature.currentIndex()
        #if index == 0:
        #    return QWebEnginePage.notifications
        if index == 0:
            return QWebEnginePage.Geolocation
        pass
