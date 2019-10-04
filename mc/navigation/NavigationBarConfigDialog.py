from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QDialogButtonBox
from mc.tools.ToolButton import ToolButton
from mc.app.Settings import Settings
from mc.common.globalvars import gVar

class NavigationBarConfigDialog(QDialog):
    def __init__(self, navigationBar):
        '''
        @param: NavigationBar
        '''
        super().__init__(navigationBar)

        self._ui = uic.loadUi('mc/navigation/NavigationBarConfigDialog.ui', self)
        self._navigationBar = navigationBar
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._ui.buttonBox.clicked.connect(self._buttonClicked)
        self._loadSettings()

    # private
    def _loadSettings(self):
        def createItem(data):
            '''
            @param: data NavigationBar.WidgetData
            '''
            item = QListWidgetItem()
            item.setText(data.name)
            item.setData(Qt.UserRole + 10, data.id)
            # XXX: Crashes in Qt on items drag&drop...
            # ToolButton
            button = data.widget
            if isinstance(button, ToolButton):
                item.setIcon(button.icon)
            return item

        self._ui.currentItems.clear()
        for id_ in self._navigationBar._layoutIds:
            # NavigationBar::WidgetData
            data = self._navigationBar._widgets.get(id_)
            if not data:
                continue
            if not data.id:
                data.id = id_
                data.name = id_
            self._ui.currentItems.addItem(createItem(data))

        self._ui.availableItems.clear()
        for data in self._navigationBar._widgets.values():
            if data.id not in self._navigationBar._layoutIds:
                self._ui.availableItems.addItem(createItem(data))

        self._ui.showSearchBar.setChecked(self._navigationBar.webSearchBar().isVisible())

    def _saveSettings(self):
        ids = []
        for idx in range(self._ui.currentItems.count()):
            ids.append(self._ui.currentItems.item(idx).data(Qt.UserRole + 10))

        settings = Settings()
        settings.beginGroup('NavigationBar')
        settings.setValue('Layout', ids)
        settings.setValue('ShowSearchBar', self._ui.showSearchBar.isChecked())
        settings.endGroup()

        windows = gVar.app.windows()
        for window in windows:
            window.navigationBar()._loadSettings()

    def _resetToDefaults(self):
        settings = Settings()
        settings.beginGroup('NavigationBar')
        settings.remove('Layout')
        settings.remove('ShowSearchBar')
        settings.endGroup()

        windows = gVar.app.windows()
        for window in windows:
            window.navigationBar()._loadSettings()

    def _buttonClicked(self, button):
        '''
        @param: button QAbstractButton
        '''
        btnRole = self._ui.buttonBox.buttonRole(button)
        if btnRole == QDialogButtonBox.ApplyRole:
            self._saveSettings()
            self._loadSettings()
        elif btnRole == QDialogButtonBox.RejectRole:
            self.close()
        elif btnRole == QDialogButtonBox.ResetRole:
            self._resetToDefaults()
            self._loadSettings()
        elif btnRole == QDialogButtonBox.AcceptRole:
            self._saveSettings()
            self.close()
