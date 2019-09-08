from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIcon
from PyQt5.QtWidgets import QMessageBox
from mc.common.globalvars import gVar
from mc.tools.IconProvider import IconProvider
from mc.app.Settings import Settings
from mc.other.CheckBoxDialog import CheckBoxDialog

class TabContextMenu(QMenu):
    # enum Option
    InvalidOption = 0
    HorizontalTabs = 1 << 0
    VerticalTabs = 1 << 1
    ShowCloseOtherTabsActions = 1 << 2
    ShowDetachTabAction = 1 << 3
    DefaultOptions = HorizontalTabs | ShowCloseOtherTabsActions
    def __init__(self, index, window, options=DefaultOptions):
        super().__init__()
        self._clickedTab = index  # int
        self._window = window  # BrowserWindow
        self._options = options

        self.setObjectName('tabcontextmenu')
        tabWidget = self._window.tabWidget()
        self.tabCloseRequested.connect(tabWidget.tabBar().tabCloseRequested)
        self.reloadTab.connect(tabWidget.reloadTab)
        self.stopTab.connect(tabWidget.stopTab)
        self.closeAllButCurrent.connect(tabWidget.closeAllButCurrent)
        self.closeToRight.connect(tabWidget.closeToRight)
        self.closeToLeft.connect(tabWidget.closeToLeft)
        self.duplicateTab.connect(tabWidget.duplicateTab)
        self.detachTab.connect(tabWidget.detachTab)
        self.loadTab.connect(tabWidget.loadTab)
        self.unloadTab.connect(tabWidget.unloadTab)

        self._init()

    def _init(self):
        tabWidget = self._window.tabWidget()
        if self._clickedTab != -1:
            webTab = tabWidget.webTab(self._clickedTab)
            if not webTab:
                return

            if webTab.webView().isLoading():
                self.addAction(QIcon.fromTheme('process-stop'), _('&Stop Tab'),
                        self._stopTab)
            else:
                self.addAction(QIcon.fromTheme('view-refresh'), _('&Reload Tab'),
                        self._reloadTab)

            self.addAction(QIcon.fromTheme('tab-duplicate'), _('&Duplicate Tab'),
                    self._duplicateTab)

            if self._options & self.ShowDetachTabAction and (gVar.app.windowCount() > 1 or
                    tabWidget.count() > 1):
                self.addAction(QIcon.fromTheme('tab-detach'), _('D&etach Tab'),
                        self._detachTab)

            self.addAction(webTab.isPinned() and _('Un&pin Tab') or _('&Pin Tab'), self._pinTab)
            self.addAction(webTab.isMuted() and _('Un&mute Tab') or _('&Mute Tab'), self._muteTab)

            if not webTab.isRestored():
                self.addAction(_('Load Tab'), self._loadTab)
            else:
                self.addAction(_('Unload Tab'), self._unloadTab)

            self.addSeparator()
            self.addAction(_('Re&load All Tabs'), tabWidget.reloadAllTabs)
            self.addAction(_('Bookmark &All Tabs'), self._window.bookmarkAllTabs)
            self.addSeparator()

            if self._options & self.ShowCloseOtherTabsActions:
                self.addAction(_('Close Ot&her Tabs'), self._closeAllButCurrent)
                self.addAction(self._options & self.HorizontalTabs and _('Close Tabs To The Right') or
                        _('Close Tabs To The Bottom'), self._closeToRight)
                self.addAction(self._options & self.HorizontalTabs and _('Close Tabs To The Left') or
                        _('Close Tabs To The Top'), self._closeToLeft)
                self.addSeparator()

            self.addAction(self._window.action('Other/RestoreClosedTab'))
            self.addAction(QIcon.fromTheme('window-close'), _('Cl&ose Tab'), self._closeTab)
        else:
            self.addAction(IconProvider.newTabIcon(), _('&New tab'), self._window.addTab)
            self.addSeparator()
            self.addAction(_('Reloa&d All Tabs'), tabWidget.reloadAllTabs)
            self.addAction(_('Bookmark &All Tabs'), self._window.bookmarkAllTabs)
            self.addSeparator()
            self.addAction(self._window.action('Other/RestoreClosedTab'))

        self._window.action('Other/RestoreClosedTab').setEnabled(tabWidget.canRestoreTab())

        self.aboutToHide.connect(lambda: self._window.action('Other/RestoreClosedTab').setEnabled(True))

    # Q_SIGNALS:
    reloadTab = pyqtSignal(int)  # index
    stopTab = pyqtSignal(int)  # index
    tabCloseRequested = pyqtSignal(int)  # index
    closeAllButCurrent = pyqtSignal(int)  # index
    closeToRight = pyqtSignal(int)  # index
    closeToLeft = pyqtSignal(int)  # index
    duplicateTab = pyqtSignal(int)  # index
    detachTab = pyqtSignal(int)  # index
    loadTab = pyqtSignal(int)  # index
    unloadTab = pyqtSignal(int)  # index

    # private Q_SLOTS:
    def _reloadTab(self):
        self.reloadTab.emit(self._clickedTab)

    def _stopTab(self):
        self.stopTab.emit(self._clickedTab)

    def _closeTab(self):
        self.tabCloseRequested.emit(self._clickedTab)

    def _duplicateTab(self):
        self.duplicateTab.emit(self._clickedTab)

    def _detachTab(self):
        self.detachTab.emit(self._clickedTab)

    def _loadTab(self):
        self.loadTab.emit(self._clickedTab)

    def _unloadTab(self):
        self.unloadTab.emit(self._clickedTab)

    def _pinTab(self):
        webTab = self._window.tabWidget().webTab(self._clickedTab)
        if webTab:
            webTab.togglePinned()

    def _muteTab(self):
        webTab = self._window.tabWidget().webTab(self._clickedTab)
        if webTab:
            webTab.toggleMuted()

    @classmethod
    def canCloseTabs(cls, settingsKey, title, description):
        settings = Settings()
        ask = settings.value('Browser-Tabs-Settings/'+settingsKey, True, type=bool)

        if ask:
            dialog = CheckBoxDialog(QMessageBox.Yes | QMessageBox.No, gVar.app.activeWindow())
            dialog.setDefaultButton(QMessageBox.No)
            dialog.setWindowTitle(title)
            dialog.setText(description)
            dialog.setCheckBoxText(_("Don't ask again"))
            dialog.setIcon(QMessageBox.Question)

            if dialog.exec_() != QMessageBox.Yes:
                return False

            if dialog.isChecked():
                settings.setValue('Browser-Tabs-Settings/'+settingsKey, False)

        return True

    def _closeAllButCurrent(self):
        if self.canCloseTabs('AskOnClosingAllButCurrent', _('Close Tabs'),
                _('Do you really want to close other tabs?')):
            self.closeAllButCurrent.emit(self._clickedTab)

    def _closeToRight(self):
        label = self._options & self.HorizontalTabs and \
            _('Do you really want to close all tabs to the right?') or \
            _('Do you really want to close all tabs to the bottom?')

        if self.canCloseTabs('AskOnClosingToRight', _('Close Tabs'), label):
            self.closeToRight.emit(self._clickedTab)

    def _closeToLeft(self):
        label = self._options & self.HorizontalTabs and \
            _('Do you really want to close all tabs to the left?') or \
            _('Do you really want to close all tabs to the top?')

        if self.canCloseTabs('AskOnClosingToLeft', _('Close Tabs'), label):
            self.closeToRight.emit(self._clickedTab)
