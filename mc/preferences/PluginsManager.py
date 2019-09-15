from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.Qt import Qt
from mc.tools.IconProvider import IconProvider

class PluginsManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/preferences/PluginsList.ui', self)
        self._ui.list.setLayoutDirection(Qt.LeftToRight)
        self._ui.butSettings.setIcon(IconProvider.settingsIcon())

        # TODO:

    def load(self):
        pass

    def save(self):
        pass

    # private Q_SLOTS:
    def _settingsClicked(self):
        pass

    def _currentChanged(self, item):
        '''
        @param: item QListWidgetItem
        '''
        pass

    def _itemChanged(self, item):
        '''
        @param: item QListWidgetItem
        '''
        pass

    def _refresh(self):
        pass

    # private:
    def _sortItems(self):
        pass
