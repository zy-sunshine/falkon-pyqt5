from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QIcon
from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.Qt import QFile, QFileInfo

from mc.app.Settings import Settings
from mc.common import const
from mc.app.DataPaths import DataPaths
from mc.common.globalvars import gVar
from mc.tools.DesktopFile import DesktopFile

class ThemeManager(QWidget):
    class _Theme:
        def __init__(self):
            self.isValid = False
            self.icon = QIcon()
            self.name = ''
            self.author = ''
            self.description = ''
            self.license = ''

    def __init__(self, parent, preferences):
        '''
        @param: parent QWidget
        @param: preferences Preferences
        '''
        super().__init__()
        self._ui = uic.loadUi('mc/preferences/ThemeManager.ui', self)
        self._preferences = preferences  # Preferences

        self._activeTheme = ''
        self._themeHash = {}  # QHash<QString, Theme>

        self._ui.listWidget.setLayoutDirection(Qt.LeftToRight)
        self._ui.license.hide()

        settings = Settings()
        settings.beginGroup('Themes')
        self._activeTheme = settings.value('activeTheme', const.DEFAULT_THEME_NAME)
        settings.endGroup()

        themePaths = DataPaths.allPaths(DataPaths.Themes)

        for path in themePaths:
            dir_ = QDir(path)
            list_ = dir_.entryList(QDir.AllDirs | QDir.NoDotAndDotDot)
            for name in list_:
                # Theme
                themeInfo = self._parseTheme(dir_.absoluteFilePath(name) + '/', name)
                if not themeInfo.isValid:
                    continue

                item = QListWidgetItem(self._ui.listWidget)
                item.setText(themeInfo.name)
                item.setIcon(themeInfo.icon)
                item.setData(Qt.UserRole, name)

                if self._activeTheme == name:
                    self._ui.listWidget.setCurrentItem(item)

                self._ui.listWidget.addItem(item)

        self._ui.listWidget.currentItemChanged.connect(self._currentChanged)
        self._ui.license.clicked.connect(self._showLicense)

        self._currentChanged()

    def save(self):
        currentItem = self._ui.listWidget.currentItem()
        if not currentItem:
            return

        settings = Settings()
        settings.beginGroup('Themes')
        settings.setValue('activeTheme', currentItem.data(Qt.UserRole))
        settings.endGroup()

    # private Q_SLOTS:
    def _currentChanged(self):
        currentItem = self._ui.listWidget.currentItem()
        if not currentItem:
            return

        # Theme
        currentTheme = self._themeHash[currentItem.data(Qt.UserRole)]

        self._ui.name.setText(currentTheme.name)
        self._ui.author.setText(currentTheme.author)
        self._ui.description.setText(currentTheme.description)
        self._ui.license.setHidden(not currentTheme.license)

    def _showLicense(self):
        currentItem = self._ui.listWidget.currentItem()
        if not currentItem:
            return

        currentTheme = self._themeHash[currentItem.data(Qt.UserRole)]

        v = LicenseViewer(self._preferences)
        v.setText(currentTheme.license)
        v.show()

    def _parseTheme(self, path, name):
        '''
        @param: path QString
        @param: name QString
        @return self._Theme
        '''
        info = self._Theme()
        info.isValid = False

        if not QFile(path + 'main.css').exists() or not QFile(path + 'metadata.desktop').exists():
            info.isValid = False
            return info

        metadata = DesktopFile('metadata.desktop')
        info.name = metadata.name()
        info.description = metadata.comment()
        info.author = metadata.value('X-App-Author')

        # QString
        iconName = metadata.icon()
        if iconName:
            if QFileInfo.exists(path + iconName):
                info.icon = QIcon(path + iconName)
            else:
                info.icon = QIcon.fromTheme(iconName)

        licensePath = metadata.value('X-App-License')
        if licensePath and QFileInfo.exists(path + licensePath):
            info.license = gVar.appTools.readAllFileContents(path + licensePath)

        if not info.name or name in self._themeHash:
            return info

        info.isValid = True
        self._themeHash[name] = info
        return info
