from glob import glob
from os.path import basename
from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import QColor
from PyQt5 import uic
from PyQt5.Qt import QUrl
from PyQt5.Qt import QPoint
from PyQt5.Qt import Qt
from PyQt5.Qt import QIcon
from PyQt5.Qt import QSizePolicy
from PyQt5.Qt import QPalette
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.Qt import QFontDatabase
from PyQt5.Qt import QFont
from PyQt5.Qt import QDir
from PyQt5.Qt import QCoreApplication
from PyQt5.Qt import QLibraryInfo
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import QStyle
from PyQt5.Qt import QPixmap
from PyQt5.QtWidgets import QColorDialog
from PyQt5.Qt import QLocale
from PyQt5.Qt import QApplication
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QSize

from mc.common.globalvars import gVar
from mc.app.Settings import Settings
from mc.common import const
from mc.app.ProfileManager import ProfileManager
from mc.notifications.DesktopNotificationsFactory import DesktopNotificationsFactory
from .ThemeManager import ThemeManager
from .PluginsManager import PluginsManager
from .AutoFillManager import AutoFillManager

def createLanguageItem(self, lang):
    '''
    @param: lang QString
    '''
    locale = QLocale(lang)

    if locale.language() == QLocale.C:
        return lang

    country = QLocale.countryToString(locale.country())
    language = QLocale.languageToString(locale.language())

    if lang == "es_ES":
        return "Castellano"
    if lang == "nqo":
        return "N'ko (nqo)"
    if lang == "sr":
        return "српски екавски"
    if lang == "sr@ijekavian":
        return "српски ијекавски"
    if lang == "sr@latin":
        return "srpski ekavski"
    if lang == "sr@ijekavianlatin":
        return "srpski ijekavski"
    return "%s, %s (%s)" % (language, country, lang)

class Preferences(QDialog):
    def __init__(self, window):  # noqa C901
        '''
        @param: window BrowserWindow
        '''
        super().__init__(window)

        self._ui = uic.loadUi('mc/preferences/Preferences.ui', self)
        self._window = window
        self._autoFillManager = None  # AutoFillManager
        self._pluginsList = None  # PluginsManager
        self._themesManager = None  # ThemeManager
        self._notification = None  # QPointer<DesktopNotification>

        self._homePage = QUrl()
        self._newTabUrl = QUrl()
        self._actProfileName = ''
        self._afterLaunch = 0
        self._onNewTab = 0
        self._notifPosition = QPoint()

        self.setAttribute(Qt.WA_DeleteOnClose)
        gVar.appTools.centerWidgetOnScreen(self)

        self._themesManager = ThemeManager(self._ui.themesWidget, self)
        self._pluginsList = PluginsManager(self)
        self._ui.pluginsFrame.addWidget(self._pluginsList)

        # #ifdef DISABLE_CHECK_UPDATES
        #     ui->checkUpdates->setVisible(false);
        # #endif
        #
        # #if QTWEBENGINEWIDGETS_VERSION < QT_VERSION_CHECK(5, 11, 0)
        #     ui->disableVideoAutoPlay->setVisible(false);
        #     ui->webRTCPublicIpOnly->setVisible(false);
        # #endif
        #
        # #if QTWEBENGINEWIDGETS_VERSION < QT_VERSION_CHECK(5, 12, 0)
        #     ui->dnsPrefetch->setVisible(false);
        # #endif

        def setCategoryIcon(index, icon):
            '''
            @param: index int
            @param: icon QIcon
            '''
            self._ui.listWidget.item(index).setIcon(QIcon(icon.pixmap(32)))

        setCategoryIcon(0, QIcon(":/icons/preferences/general.svg"))
        setCategoryIcon(1, QIcon(":/icons/preferences/appearance.svg"))
        setCategoryIcon(2, QIcon(":/icons/preferences/tabs.svg"))
        setCategoryIcon(3, QIcon(":/icons/preferences/browsing.svg"))
        setCategoryIcon(4, QIcon(":/icons/preferences/fonts.svg"))
        setCategoryIcon(5, QIcon(":/icons/preferences/shortcuts.svg"))
        setCategoryIcon(6, QIcon(":/icons/preferences/downloads.svg"))
        setCategoryIcon(7, QIcon(":/icons/preferences/passwords.svg"))
        setCategoryIcon(8, QIcon(":/icons/preferences/privacy.svg"))
        setCategoryIcon(9, QIcon(":/icons/preferences/notifications.svg"))
        setCategoryIcon(10, QIcon(":/icons/preferences/extensions.svg"))
        setCategoryIcon(11, QIcon(":/icons/preferences/spellcheck.svg"))
        setCategoryIcon(12, QIcon(":/icons/preferences/other.svg"))

        settings = Settings()
        # GENERAL URLs
        settings.beginGroup('Web-URL-Settings')
        self._homepage = settings.value('homepage', QUrl('app:start'), type=QUrl)
        self._newTabUrl = settings.value('newTabUrl', QUrl('app:speeddial'), type=QUrl)

        self._ui.homepage.setText(self._homepage.toEncoded().data().decode())
        self._ui.newTabUrl.setText(self._newTabUrl.toEncoded().data().decode())
        settings.endGroup()

        self._ui.afterLaunch.setCurrentIndex(gVar.app.afterLaunch())
        self._ui.checkUpdates.setChecked(settings.value('Web-Browser-Settings/CheckUpdates', True, type=bool))
        self._ui.dontLoadTabsUntilSelected.setChecked(
            settings.value('Web-Browser-Settings/LoadTabsOnActivation', True, type=bool)
        )

        if const.OS_WIN:
            if not gVar.app.isPortable():
                self._ui.checkDefaultBrowser.setChecked(
                    settings.value('Web-Browser-Settings/CheckDefaultBrowser',
                        const.DEFAULT_CHECK_DEFAULTBROWSER, type=bool)
                )

                if gVar.app.associationManager().isDefaultForAllCapabilities():
                    self._ui.checkNowDefaultBrowser.setText(_('Default'))
                    self._ui.checkNowDefaultBrowser.setEnabled(False)
                else:
                    self._ui.checkNowDefaultBrowser.setText(_('Set as default'))
                    self._ui.checkNowDefaultBrowser.setEnabled(True)
                    self._ui.checkNowDefaultBrowser.clicked.connet(self._makeAppDefault)
            else:
                self._ui.checkDefaultBrowser.hide()
                self._ui.checkNowDefaultBrowser.hide()

        else:
            # No Default Browser settings on non-Windows platform
            self._ui.hSpacerDefaultBrowser.changeSize(0, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
            self._ui.hLayoutDefaultBrowser.invalidate()
            del self._ui.hLayoutDefaultBrowser
            del self._ui.checkDefaultBrowser
            del self._ui._checkNowDefaultBrowser

        self._ui.newTabFrame.setVisible(False)
        if self._newTabUrl.isEmpty() or self._newTabUrl.toString() == 'about:blank':
            self._ui.newTab.setCurrentIndex(0)
        elif self._newTabUrl == self._homepage:
            self._ui.newTab.setCurrentIndex(1)
        elif self._newTabUrl.toString() == 'app:speeddial':
            self._ui.newTab.setCurrentIndex(2)
        else:
            self._ui.newTab.setCurrentIndex(3)
            self._ui.newTabFrame.setVisible(True)

        self._afterLaunchChanged(self._ui.afterLaunch.currentIndex())
        self._ui.afterLaunch.currentIndexChanged.connect(self._afterLaunchChanged)
        self._ui.newTab.currentIndexChanged.connect(self._newTabChanged)
        if self._window:
            self._ui.useCurrentBut.clicked.connect(self._useActualHomepage)
            self._ui.newTabUseCurrent.clicked.connect(self._useActualNewTab)
        else:
            self._ui.useCurrentBut.setEnabled(False)
            self._ui.newTabUseCurrent.setEnabled(False)

        # PROFILES
        startingProfile = ProfileManager.startingProfile()
        self._ui.activeProfile.setText('<b>' + ProfileManager.currentProfile() + '</b>')
        self._ui.startProfile.addItem(startingProfile)

        for name in ProfileManager.availableProfiles():
            if startingProfile != name:
                self._ui.startProfile.addItem(name)

        self._ui.createProfile.clicked.connect(self._createProfile)
        self._ui.deleteProfile.clicked.connect(self._deleteProfile)
        self._ui.startProfile.currentIndexChanged.connect(self._startProfileIndexChanged)
        self._startProfileIndexChanged(self._ui.startProfile.currentIndex())

        # APPEARANCE
        settings.beginGroup('Browser-View-Settings')
        self._ui.showStatusbar.setChecked(settings.value('showStatusBar', False, type=bool))
        # NOTE: instantBookmarksToolbar and showBookmarksToolbar cannot be both
        # enabled at the same time
        self._ui.instantBookmarksToolbar.setChecked(settings.value('instantBookmarksToolbar', False, type=bool))
        self._ui.showBookmarksToolbar.setChecked(settings.value('showBookmarksToolbar', False, type=bool))
        self._ui.instantBookmarksToolbar.setChecked(settings.value('showBookmarksToolbar', False, type=bool))
        self._ui.showBookmarksToolbar.setChecked(settings.value('instantBookmarksToolbar', False, type=bool))

        self._ui.instantBookmarksToolbar.toggled.connect(self._ui.showBookmarksToolbar.setDisabled)
        self._ui.showBookmarksToolbar.toggled.connect(self._ui.instantBookmarksToolbar.setDisabled)

        self._ui.showNavigationToolbar.setChecked(settings.value('showNavigationToolbar', True, type=bool))
        currentSettingsPage = settings.value('settingsDialogPage', 0, type=int)
        settings.endGroup()

        # TABS
        settings.beginGroup('Browser-Tabs-Settings')
        self._ui.hideTabsOnTab.setChecked(settings.value('hideTabsWithOneTab', False, type=bool))
        self._ui.activateLastTab.setChecked(settings.value('ActivateLastTabWhenClosingActual', False, type=bool))
        self._ui.openNewTabAfterActive.setChecked(settings.value('newTabAfterActive', True, type=bool))
        self._ui.openNewEmptyTabAfterActive.setChecked(settings.value('newEmptyTabAfterActive', False, type=bool))
        self._ui.openPopupsInTabs.setChecked(settings.value("OpenPopupsInTabs", False, type=bool))
        self._ui.alwaysSwitchTabsWithWheel.setChecked(settings.value("AlwaysSwitchTabsWithWheel", False, type=bool))
        self._ui.switchToNewTabs.setChecked(settings.value("OpenNewTabsSelected", False, type=bool))
        self._ui.dontCloseOnLastTab.setChecked(settings.value("dontCloseWithOneTab", False, type=bool))
        self._ui.askWhenClosingMultipleTabs.setChecked(settings.value("AskOnClosing", False, type=bool))
        self._ui.showClosedTabsButton.setChecked(settings.value("showClosedTabsButton", False, type=bool))
        self._ui.showCloseOnInactive.setCurrentIndex(settings.value("showCloseOnInactiveTabs", 0, type=int))
        settings.endGroup()

        # AddressBar
        settings.beginGroup("AddressBar")
        self._ui.addressbarCompletion.setCurrentIndex(settings.value("showSuggestions", 0, type=int))
        self._ui.useInlineCompletion.setChecked(settings.value("useInlineCompletion", True, type=bool))
        self._ui.completionShowSwitchTab.setChecked(settings.value("showSwitchTab", True, type=bool))
        self._ui.alwaysShowGoIcon.setChecked(settings.value("alwaysShowGoIcon", False, type=bool))
        self._ui.selectAllOnFocus.setChecked(settings.value("SelectAllTextOnDoubleClick", True, type=bool))
        self._ui.selectAllOnClick.setChecked(settings.value("SelectAllTextOnClick", False, type=bool))
        showPBinAB = settings.value("ShowLoadingProgress", True, type=bool)
        self._ui.showLoadingInAddressBar.setChecked(showPBinAB)
        self._ui.adressProgressSettings.setEnabled(showPBinAB)
        self._ui.progressStyleSelector.setCurrentIndex(settings.value("ProgressStyle", 0, type=int))
        pbInABuseCC = settings.value("UseCustomProgressColor", False, type=bool)
        self._ui.checkBoxCustomProgressColor.setChecked(pbInABuseCC)
        self._ui.progressBarColorSelector.setEnabled(pbInABuseCC)
        pbColor = settings.value("CustomProgressColor", self.palette().color(QPalette.Highlight), type=QColor)
        self._setProgressBarColorIcon(pbColor)
        self._ui.customColorToolButton.clicked.connect(self._selectCustomProgressBarColor)
        self._ui.resetProgressBarcolor.clicked.connect(lambda: self._setProgressBarColorIcon())
        settings.endGroup()

        settings.beginGroup("SearchEngines")
        searchFromAB = settings.value("SearchFromAddressBar", True, type=bool)
        self._ui.searchFromAddressBar.setChecked(searchFromAB)
        self._ui.searchWithDefaultEngine.setEnabled(searchFromAB)
        self._ui.searchWithDefaultEngine.setChecked(settings.value("SearchWithDefaultEngine", False, type=bool))
        self._ui.showABSearchSuggestions.setEnabled(searchFromAB)
        self._ui.showABSearchSuggestions.setChecked(settings.value("showSearchSuggestions", True, type=bool))
        self._ui.searchFromAddressBar.toggled.connect(self._searchFromAddressBarChanged)
        settings.endGroup()

        # BROWSING
        settings.beginGroup("Web-Browser-Settings")
        self._ui.allowPlugins.setChecked(settings.value("allowPlugins", True))
        self._ui.allowJavaScript.setChecked(settings.value("allowJavaScript", True))
        self._ui.linksInFocusChain.setChecked(settings.value("IncludeLinkInFocusChain", False))
        self._ui.spatialNavigation.setChecked(settings.value("SpatialNavigation", False))
        self._ui.animateScrolling.setChecked(settings.value("AnimateScrolling", True))
        self._ui.wheelScroll.setValue(settings.value("wheelScrollLines", gVar.app.wheelScrollLines(), type=int))
        self._ui.xssAuditing.setChecked(settings.value("XSSAuditing", False))
        self._ui.printEBackground.setChecked(settings.value("PrintElementBackground", True))
        self._ui.useNativeScrollbars.setChecked(settings.value("UseNativeScrollbars", False))
        self._ui.disableVideoAutoPlay.setChecked(settings.value("DisableVideoAutoPlay", False))
        self._ui.webRTCPublicIpOnly.setChecked(settings.value("WebRTCPublicIpOnly", True))
        self._ui.dnsPrefetch.setChecked(settings.value("DNSPrefetch", True))

        from mc.webengine.WebView import WebView
        for level in WebView.zoomLevels():
            self._ui.defaultZoomLevel.addItem("%s%%" % level)
        self._ui.defaultZoomLevel.setCurrentIndex(settings.value("DefaultZoomLevel",
            WebView.zoomLevels().index(100), type=int))
        self._ui.closeAppWithCtrlQ.setChecked(settings.value("closeAppWithCtrlQ", True))

        # Cache
        self._ui.allowCache.setChecked(settings.value("AllowLocalCache", True))
        self._ui.removeCache.setChecked(settings.value("deleteCacheOnClose", False))
        self._ui.cacheMB.setValue(settings.value("LocalCacheSize", 50))
        self._ui.cachePath.setText(settings.value("CachePath",
            QWebEngineProfile.defaultProfile().cachePath(), type=str))
        self._ui.allowCache.clicked.connect(self._allowCacheChanged)
        self._ui.changeCachePath.clicked.connect(self._changeCachePathClicked)
        self._allowCacheChanged(self._ui.allowCache.isChecked())

        # PASSWORD MANAGER
        self._ui.allowPassManager.setChecked(settings.value("SavePasswordsOnSites", True))
        self._ui.autoCompletePasswords.setChecked(settings.value("AutoCompletePasswords", True))

        # PRIVACY
        # Web storage
        self._ui.saveHistory.setChecked(settings.value("allowHistory", True))
        self._ui.deleteHistoryOnClose.setChecked(settings.value("deleteHistoryOnClose", False))
        if not self._ui.saveHistory.isChecked():
            self._ui.deleteHistoryOnClose.setEnabled(False)
        self._ui.saveHistory.toggled.connect(self._saveHistoryChanged)

        # Html5Storage
        self._ui.html5storage.setChecked(settings.value("HTML5StorageEnabled", True))
        self._ui.deleteHtml5storageOnClose.setChecked(settings.value("deleteHTML5StorageOnClose", False))
        self._ui.html5storage.toggled.connect(self._allowHtml5storageChanged)
        # Other
        self._ui.doNotTrack.setChecked(settings.value("DoNotTrack", False))

        # CSS Style
        self._ui.userStyleSheet.setText(settings.value("userStyleSheet", ""))
        self._ui.chooseUserStylesheet.clicked.connect(self._chooseUserStyleClicked)
        settings.endGroup()

        # DOWNLOADS
        settings.beginGroup("DownloadManager")
        self._ui.downLoc.setText(settings.value("defaultDownloadPath", ""))
        self._ui.closeDownManOnFinish.setChecked(settings.value("CloseManagerOnFinish", False))
        if not self._ui.downLoc.text():
            self._ui.askEverytime.setChecked(True)
        else:
            self._ui.useDefined.setChecked(True)
        self._ui.useExternalDownManager.setChecked(settings.value("UseExternalManager", False))
        self._ui.externalDownExecutable.setText(settings.value("ExternalManagerExecutable", ""))
        self._ui.externalDownArguments.setText(settings.value("ExternalManagerArguments", ""))

        self._ui.useExternalDownManager.toggled.connect(self._useExternalDownManagerChanged)

        self._ui.useDefined.toggled.connect(self._downLocChanged)
        self._ui.downButt.clicked.connect(self._chooseDownPath)
        self._ui.chooseExternalDown.clicked.connect(self._chooseExternalDownloadManager)
        self._downLocChanged(self._ui.useDefined.isChecked())
        self._useExternalDownManagerChanged(self._ui.useExternalDownManager.isChecked())
        settings.endGroup()

        # FONTS
        settings.beginGroup("Browser-Fonts")
        # QWebEngineSettings
        webSettings = gVar.app.webSettings()

        def defaultFont(font):
            '''
            @param: font QWebEngineSettings.FontFamily
            @return: QString
            '''
            # QString
            family = webSettings.fontFamily(font)
            if family:
                return family
            if font == QWebEngineSettings.FixedFont:
                return QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
            elif font == QWebEngineSettings.SerifFont:
                # TODO:
                pass
            return QFontDatabase.systemFont(QFontDatabase.GeneralFont).family()

        self._ui.fontStandard.setCurrentFont(QFont(settings.value("StandardFont",
            defaultFont(QWebEngineSettings.StandardFont))))
        self._ui.fontCursive.setCurrentFont(QFont(settings.value("CursiveFont",
            defaultFont(QWebEngineSettings.CursiveFont))))
        self._ui.fontFantasy.setCurrentFont(QFont(settings.value("FantasyFont",
            defaultFont(QWebEngineSettings.FantasyFont))))
        self._ui.fontFixed.setCurrentFont(QFont(settings.value("FixedFont",
            defaultFont(QWebEngineSettings.FixedFont))))
        self._ui.fontSansSerif.setCurrentFont(QFont(settings.value("SansSerifFont",
            defaultFont(QWebEngineSettings.SansSerifFont))))
        self._ui.fontSerif.setCurrentFont(QFont(settings.value("SerifFont",
            defaultFont(QWebEngineSettings.SerifFont))))
        self._ui.sizeDefault.setValue(settings.value("DefaultFontSize",
            webSettings.fontSize(QWebEngineSettings.DefaultFontSize), type=int))
        self._ui.sizeFixed.setValue(settings.value("FixedFontSize",
            webSettings.fontSize(QWebEngineSettings.DefaultFixedFontSize), type=int))
        self._ui.sizeMinimum.setValue(settings.value("MinimumFontSize",
            webSettings.fontSize(QWebEngineSettings.MinimumFontSize), type=int))
        self._ui.sizeMinimumLogical.setValue(settings.value("MinimumLogicalFontSize",
            webSettings.fontSize(QWebEngineSettings.MinimumLogicalFontSize), type=int))
        settings.endGroup()

        # NOTIFICATIONS
        self._ui.useNativeSystemNotifications.setEnabled(gVar.app.desktopNotifications().supportsNativeNotifications())

        # DesktopNotificationsFactory.Type
        notifyType = 0
        settings.beginGroup("Notifications")
        self._ui.notificationTimeout.setValue(settings.value("Timeout", 6000) / 1000)
        if const.OS_LINUX:  # and not const.DISABLE_DBUS
            if settings.value("UseNativeDesktop", True):
                notifyType = DesktopNotificationsFactory.DesktopNative
            else:
                notifyType = DesktopNotificationsFactory.PopupWidget
        else:
            notifyType = DesktopNotificationsFactory.PopupWidget
        if self._ui.useNativeSystemNotifications.isEnabled() and \
                notifyType == DesktopNotificationsFactory.DesktopNative:
            self._ui.useNativeSystemNotifications.setChecked(True)
        else:
            self._ui.useOSDNotifications.setChecked(True)

        self._ui.notificationPreview.clicked.connect(self._showNotificationPreview)

        self._ui.doNotUseNotifications.setChecked(not settings.value("Enabled", True))
        self._notifPosition = settings.value("Position", QPoint(10, 10), type=QPoint)
        settings.endGroup()

        # SPELLCHECK
        settings.beginGroup('SpellCheck')
        self._ui.spellcheckEnabled.setChecked(settings.value('Enabled', False))
        spellcheckLanguages = settings.value('Languages', type=list)  # toStringList()
        settings.endGroup()

        def updateSpellCheckEnabled():
            self._ui.spellcheckLanguages.setEnabled(self._ui.spellcheckEnabled.isChecked())
            self._ui.spellcheckNoLanguages.setEnabled(self._ui.spellcheckEnabled.isChecked())

        updateSpellCheckEnabled()
        self._ui.spellcheckEnabled.toggled.connect(updateSpellCheckEnabled)

        dictionariesDirs = []
        if const.OS_MACOS:
            dictionariesDirs = [
                QDir.cleanPath(QCoreApplication.applicationDirPath() +
                    '/../Resources/qtwebengine_dictionaries'),
                QDir.cleanPath(QCoreApplication.applicationDirPath() +
                    "/../Frameworks/QtWebEngineCore.framework/Resources/qtwebengine_dictionaries")
            ]
        else:
            dictionariesDirs = [
                QDir.cleanPath(QCoreApplication.applicationDirPath() +
                    "/qtwebengine_dictionaries"),
                QDir.cleanPath(QLibraryInfo.location(QLibraryInfo.DataPath) +
                    "/qtwebengine_dictionaries")
            ]

        dictionariesDirs = list(set(dictionariesDirs))

        self._ui.spellcheckDirectories.setText('\n'.join(dictionariesDirs))

        for path in dictionariesDirs:
            files = [ basename(item) for item in glob(path+'/*.bdic') ]
            for fname in files:
                lang = fname[:-5]
                langName = createLanguageItem(lang)
                if not self._ui.spellcheckLanguages.findItems(langName, Qt.MatchExactly):
                    continue
                item = QListWidgetItem()
                item.setText(langName)
                item.setData(Qt.UserRole, lang)
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                item.setCheckState(Qt.Unchecked)
                self._ui.spellcheckLanguages.addItem(item)

        # put all settings language top and checked
        topIndex = 0
        for lang in spellcheckLanguages:
            langName = createLanguageItem(lang)
            items = self._ui.spellcheckLanguages.findItems(langName, Qt.MatchExactly)
            if not items:
                continue
            # QListWidgetItem
            item = items[0]
            self._ui.spellcheckLanguages.takeItem(self._ui.spellcheckLanguages.row(item))
            self._ui.spellcheckLanguages.insertItem(topIndex, item)
            topIndex += 1
            item.setCheckState(Qt.Checked)

        if self._ui.spellcheckLanguages.count() == 0:
            self._ui.spellcheckLanguages.hide()
        else:
            self._ui.spellcheckNoLanguages.hide()

        # Proxy Configuration
        settings.beginGroup('Web-Proxy')
        proxyType = settings.value('ProxyType', 2)
        if proxyType == 0:
            self._ui.noProxy.setChecked(True)
        elif proxyType == 2:
            self._ui.systemProxy.setChecked(True)
        elif proxyType == 3:
            self._ui.manualProxy.setChecked(True)
            self._ui.proxyType.setCurrentIndex(0)
        else:
            self._ui.manualProxy.setChecked(True)
            self._ui.proxyType.setCurrentIndex(1)

        self._ui.proxyServer.setText(settings.value('HostName', ''))
        self._ui.proxyPort.setText(str(settings.value('Port', 8080)))
        self._ui.proxyUsername.setText(settings.value('Username', ''))
        self._ui.proxyPassword.setText(settings.value('Password', ''))
        settings.endGroup()

        self._setManualProxyConfigurationEnabled(self._ui.manualProxy.isChecked())
        self._ui.manualProxy.toggled.connect(self._setManualProxyConfigurationEnabled)

        # CONNECCTS
        self._ui.buttonBox.clicked.connect(self._buttonClicked)
        self._ui.cookieManagerBut.clicked.connect(self._showCookieManager)
        self._ui.html5permissions.clicked.connect(self._showHtml5Permissions)
        self._ui.preferredLanguages.clicked.connect(self._showAcceptLanguage)
        self._ui.deleteHtml5storage.clicked.connect(self._deleteHtml5storage)
        self._ui.uaManager.clicked.connect(self._openUserAgentManager)
        self._ui.jsOptionsButton.clicked.connect(self._openJsOptions)
        self._ui.searchEngines.clicked.connect(self._openSearchEnginesManager)
        self._ui.protocolHandlers.clicked.connect(self._openProtocolHandlersManager)

        self._ui.listWidget.currentItemChanged.connect(self._showStackedPage)
        self._ui.listWidget.itemAt(5, 5).setSelected(True)

        self._ui.listWidget.setCurrentRow(currentSettingsPage)

        # QDesktopWidget*
        desktop = QApplication.desktop()
        s = self.size()
        if desktop.availableGeometry(self).size().width() < s.width():
            s.setWidth(desktop.availableGeometry(self).size().width() - 50)
        if desktop.availableGeometry(self).size().height() < s.height():
            s.setHeight(desktop.availableGeometry(self).size().height() - 50)
        self.resize(s)

        settings.beginGroup("Preferences")
        self.restoreGeometry(settings.value("Geometry", type=QByteArray))
        settings.endGroup()

        gVar.appTools.setWmClass("Preferences", self)

    # private Q_SLOTS:
    def _saveSettings(self):  # noqa C901
        settings = Settings()
        # GENERAL URLs
        homepage = QUrl.fromUserInput(self._ui.homepage.text())

        settings.beginGroup("Web-URL-Settings")
        settings.setValue("homepage", homepage)
        settings.setValue("afterLaunch", self._ui.afterLaunch.currentIndex())

        newTabCurIdx = self._ui.newTab.currentIndex()
        if newTabCurIdx == 0:
            settings.setValue("newTabUrl", QUrl())
        elif newTabCurIdx == 1:
            settings.setValue("newTabUrl", homepage)
        elif newTabCurIdx == 2:
            settings.setValue("newTabUrl", QUrl("app:speeddial"))
        elif newTabCurIdx == 3:
            settings.setValue("newTabUrl", QUrl.fromUserInput(self._ui.newTabUrl.text()))

        settings.endGroup()
        # PROFILES

        # WINDOW
        settings.beginGroup("Browser-View-Settings")
        settings.setValue("showStatusBar", self._ui.showStatusbar.isChecked())
        settings.setValue("instantBookmarksToolbar", self._ui.instantBookmarksToolbar.isChecked())
        settings.setValue("showBookmarksToolbar", self._ui.showBookmarksToolbar.isChecked())
        settings.setValue("showNavigationToolbar", self._ui.showNavigationToolbar.isChecked())
        settings.endGroup()

        # TABS
        settings.beginGroup("Browser-Tabs-Settings")
        settings.setValue("hideTabsWithOneTab", self._ui.hideTabsOnTab.isChecked())
        settings.setValue("ActivateLastTabWhenClosingActual", self._ui.activateLastTab.isChecked())
        settings.setValue("newTabAfterActive", self._ui.openNewTabAfterActive.isChecked())
        settings.setValue("newEmptyTabAfterActive", self._ui.openNewEmptyTabAfterActive.isChecked())
        settings.setValue("OpenPopupsInTabs", self._ui.openPopupsInTabs.isChecked())
        settings.setValue("AlwaysSwitchTabsWithWheel", self._ui.alwaysSwitchTabsWithWheel.isChecked())
        settings.setValue("OpenNewTabsSelected", self._ui.switchToNewTabs.isChecked())
        settings.setValue("dontCloseWithOneTab", self._ui.dontCloseOnLastTab.isChecked())
        settings.setValue("AskOnClosing", self._ui.askWhenClosingMultipleTabs.isChecked())
        settings.setValue("showClosedTabsButton", self._ui.showClosedTabsButton.isChecked())
        settings.setValue("showCloseOnInactiveTabs", self._ui.showCloseOnInactive.currentIndex())
        settings.endGroup()

        # DOWNLOADS
        settings.beginGroup("DownloadManager")
        if self._ui.askEverytime.isChecked():
            settings.setValue("defaultDownloadPath", "")
        else:
            settings.setValue("defaultDownloadPath", self._ui.downLoc.text())
        settings.setValue("CloseManagerOnFinish", self._ui.closeDownManOnFinish.isChecked())
        settings.setValue("UseExternalManager", self._ui.useExternalDownManager.isChecked())
        settings.setValue("ExternalManagerExecutable", self._ui.externalDownExecutable.text())
        settings.setValue("ExternalManagerArguments", self._ui.externalDownArguments.text())

        settings.endGroup()

        # FONTS
        settings.beginGroup("Browser-Fonts")
        settings.setValue("StandardFont", self._ui.fontStandard.currentFont().family())
        settings.setValue("CursiveFont", self._ui.fontCursive.currentFont().family())
        settings.setValue("FantasyFont", self._ui.fontFantasy.currentFont().family())
        settings.setValue("FixedFont", self._ui.fontFixed.currentFont().family())
        settings.setValue("SansSerifFont", self._ui.fontSansSerif.currentFont().family())
        settings.setValue("SerifFont", self._ui.fontSerif.currentFont().family())

        settings.setValue("DefaultFontSize", self._ui.sizeDefault.value())
        settings.setValue("FixedFontSize", self._ui.sizeFixed.value())
        settings.setValue("MinimumFontSize", self._ui.sizeMinimum.value())
        settings.setValue("MinimumLogicalFontSize", self._ui.sizeMinimumLogical.value())
        settings.endGroup()

        # KEYBOARD SHORTCUTS
        settings.beginGroup("Shortcuts")
        settings.setValue("useTabNumberShortcuts", self._ui.switchTabsAlt.isChecked())
        settings.setValue("useSpeedDialNumberShortcuts", self._ui.loadSpeedDialsCtrl.isChecked())
        settings.setValue("useSingleKeyShortcuts", self._ui.singleKeyShortcuts.isChecked())
        settings.endGroup()

        # BROWSING
        settings.beginGroup("Web-Browser-Settings")
        settings.setValue("allowPlugins", self._ui.allowPlugins.isChecked())
        settings.setValue("allowJavaScript", self._ui.allowJavaScript.isChecked())
        settings.setValue("IncludeLinkInFocusChain", self._ui.linksInFocusChain.isChecked())
        settings.setValue("SpatialNavigation", self._ui.spatialNavigation.isChecked())
        settings.setValue("AnimateScrolling", self._ui.animateScrolling.isChecked())
        settings.setValue("wheelScrollLines", self._ui.wheelScroll.value())
        settings.setValue("DoNotTrack", self._ui.doNotTrack.isChecked())
        settings.setValue("CheckUpdates", self._ui.checkUpdates.isChecked())
        settings.setValue("LoadTabsOnActivation", self._ui.dontLoadTabsUntilSelected.isChecked())
        settings.setValue("DefaultZoomLevel", self._ui.defaultZoomLevel.currentIndex())
        settings.setValue("XSSAuditing", self._ui.xssAuditing.isChecked())
        settings.setValue("PrintElementBackground", self._ui.printEBackground.isChecked())
        settings.setValue("closeAppWithCtrlQ", self._ui.closeAppWithCtrlQ.isChecked())
        settings.setValue("UseNativeScrollbars", self._ui.useNativeScrollbars.isChecked())
        settings.setValue("DisableVideoAutoPlay", self._ui.disableVideoAutoPlay.isChecked())
        settings.setValue("WebRTCPublicIpOnly", self._ui.webRTCPublicIpOnly.isChecked())
        settings.setValue("DNSPrefetch", self._ui.dnsPrefetch.isChecked())

        if const.OS_WIN:
            settings.setValue("CheckDefaultBrowser", self._ui.checkDefaultBrowser.isChecked())
        # Cache
        settings.setValue("AllowLocalCache", self._ui.allowCache.isChecked())
        settings.setValue("deleteCacheOnClose", self._ui.removeCache.isChecked())
        settings.setValue("LocalCacheSize", self._ui.cacheMB.value())
        settings.setValue("CachePath", self._ui.cachePath.text())
        # CSS Style
        settings.setValue("userStyleSheet", self._ui.userStyleSheet.text())

        # PASSWORD MANAGER
        settings.setValue("SavePasswordsOnSites", self._ui.allowPassManager.isChecked())
        settings.setValue("AutoCompletePasswords", self._ui.autoCompletePasswords.isChecked())

        # PRIVACY
        # Web storage
        settings.setValue("allowHistory", self._ui.saveHistory.isChecked())
        settings.setValue("deleteHistoryOnClose", self._ui.deleteHistoryOnClose.isChecked())
        settings.setValue("HTML5StorageEnabled", self._ui.html5storage.isChecked())
        settings.setValue("deleteHTML5StorageOnClose", self._ui.deleteHtml5storageOnClose.isChecked())
        settings.endGroup()

        # NOTIFICATIONS
        settings.beginGroup("Notifications")
        settings.setValue("Timeout", self._ui.notificationTimeout.value() * 1000)
        settings.setValue("Enabled", not self._ui.doNotUseNotifications.isChecked())
        settings.setValue("UseNativeDesktop", self._ui.useNativeSystemNotifications.isChecked())
        if self._notification:
            pos = self._notification.pos()
        else:
            pos = self._notifPosition
        settings.setValue("Position", pos)
        settings.endGroup()

        # SPELLCHECK
        settings.beginGroup("SpellCheck")
        settings.setValue("Enabled", self._ui.spellcheckEnabled.isChecked())
        languages = []  # QStringList
        for idx in range(self._ui.spellcheckLanguages.count()):
            # QListWidgetItem
            item = self._ui.spellcheckLanguages.item(idx)
            if item.checkState() == Qt.Checked:
                languages.append(item.data(Qt.UserRole))
        settings.setValue("Languages", languages)
        settings.endGroup()

        # OTHER
        # AddressBar
        settings.beginGroup("AddressBar")
        settings.setValue("showSuggestions", self._ui.addressbarCompletion.currentIndex())
        settings.setValue("useInlineCompletion", self._ui.useInlineCompletion.isChecked())
        settings.setValue("alwaysShowGoIcon", self._ui.alwaysShowGoIcon.isChecked())
        settings.setValue("showSwitchTab", self._ui.completionShowSwitchTab.isChecked())
        settings.setValue("SelectAllTextOnDoubleClick", self._ui.selectAllOnFocus.isChecked())
        settings.setValue("SelectAllTextOnClick", self._ui.selectAllOnClick.isChecked())
        settings.setValue("ShowLoadingProgress", self._ui.showLoadingInAddressBar.isChecked())
        settings.setValue("ProgressStyle", self._ui.progressStyleSelector.currentIndex())
        settings.setValue("UseCustomProgressColor", self._ui.checkBoxCustomProgressColor.isChecked())
        color = self._ui.customColorToolButton.property("ProgressColor")
        settings.setValue("CustomProgressColor", color)
        settings.endGroup()

        settings.beginGroup("SearchEngines")
        settings.setValue("SearchFromAddressBar", self._ui.searchFromAddressBar.isChecked())
        settings.setValue("SearchWithDefaultEngine", self._ui.searchWithDefaultEngine.isChecked())
        settings.setValue("showSearchSuggestions", self._ui.showABSearchSuggestions.isChecked())
        settings.endGroup()

        # Proxy Configuration
        proxyType = 0
        if self._ui.noProxy.isChecked():
            proxyType = 0
        elif self._ui.systemProxy.isChecked():
            proxyType = 2
        elif self._ui.proxyType.currentIndex() == 0: # Http
            proxyType = 3
        else:  # Socks5
            proxyType = 4

        settings.beginGroup("Web-Proxy")
        settings.setValue("ProxyType", proxyType)
        settings.setValue("HostName", self._ui.proxyServer.text())
        settings.setValue("Port", int(self._ui.proxyPort.text()))
        settings.setValue("Username", self._ui.proxyUsername.text())
        settings.setValue("Password", self._ui.proxyPassword.text())
        settings.endGroup()

        ProfileManager.setStartingProfile(self._ui.startProfile.currentText())

        self._pluginsList.save()
        self._themesManager.save()
        gVar.app.cookieJar().loadSettings()
        gVar.app.history().loadSettings()
        gVar.app.reloadSettings()
        gVar.app.desktopNotifications().loadSettings()
        gVar.app.autoFill().loadSettings()
        gVar.app.networkManager().loadSettings()

        gVar.webScrollBarManager.loadSettings()

    def _buttonClicked(self, button):
        '''
        @param: button QAbstractButton
        '''
        role = self._ui.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self._saveSettings()
        elif role == QDialogButtonBox.RejectRole:
            self.close()
        elif role == QDialogButtonBox.AcceptRole:
            self._saveSettings()
            self.close()

    def _showStackedPage(self, item):
        '''
        @param: item QListWidgetItem
        '''
        if not item:
            return

        index = self._ui.listWidget.currentRow()

        self._ui.caption.setText('<b>' + item.text() + '</b>')
        self._ui.stackedWidget.setCurrentIndex(index)

        if self._notification:
            self._notifPosition = self._notification.pos()
            # TODO: del self._notification to close?
            self._notification = None

        # TODO: hardcode of index...
        if index == 10:
            self._pluginsList.load()

        if index == 7 and not self._autoFillManager:
            self._autoFillManager = AutoFillManager(self)
            self._ui.autoFillFrame.addWidget(self._autoFillManager)

    def _chooseDownPath(self):
        userFileName = gVar.appTools.getExistingDirectory('Preferences-ChooseDownPath',
                self, _('Choose download location...'), QDir.homePath())
        if not userFileName:
            return

        if const.OS_WIN:
            userFileName = userFileName.replace('\\', '/')
        userFileName += '/'

        self._ui.downLoc.setText(userFileName)

    def _showCookieManager(self):
        dialog = CookieManager(self)
        dialog.show()

    def _showHtml5Permissions(self):
        dialog = HTML5PermissionsDialog(self)
        dialog.open()

    def _useActualHomepage(self):
        if not self.window:
            return

        self._ui.homepage.setText(self._window.weView().url().toString())

    def _useActualNewTab(self):
        if not self.window:
            return

        self._ui.newTabUrl.setText(self._window.weView().url().toString())

    def _showAcceptLanguage(self):
        dialog = AcceptLanguage(self)
        dialog.open()

    def _chooseUserStyleClicked(self):
        file_ = gVar.appTools.getOpenFileName('Preferences-UserStyle', self,
            _('Choose stylesheet location...'), QDir.homePath(), '*.css')
        if not file_:
            return
        self._ui.userStyleSheet.setText(file_)

    def _deleteHtml5storage(self):
        ClearPrivateData.clearLocalStorage()

        self._ui.deleteHtml5storage.setText(_('Deleted'))
        self._ui.deleteHtml5storage.setEnabled(False)

    def _chooseExternalDownloadManager(self):
        path = gVar.app.getOpenFileName('Preferences-ExternalDownloadManager', self,
            _('Choose executable location...'), QDir.homePath())
        if not path:
            return
        self._ui.externalDownExecutable.setText(path)

    def _openUserAgentManager(self):
        dialog = UserAgentDialog(self)
        dialog.open()

    def _openJsOptions(self):
        dialog = JsOptions(self)
        dialog.open()

    def _openSearchEnginesManager(self):
        dialog = SearchEnginesDialog(self)
        dialog.open()

    def _openProtocolHandlersManager(self):
        dialog = ProtocolHandlerDialog(self)
        dialog.open()

    def _searchFromAddressBarChanged(self, state):
        self._ui.searchWithDefaultEngine.setEnabled(state)
        self._ui.showABSearchSuggestions.setEnabled(state)

    def _saveHistoryChanged(self, state):
        self._ui.deleteHistoryOnClose.setEnabled(state)

    def _allowHtml5storageChanged(self, state):
        self._ui.deleteHtml5storageOnClose.setEnabled(state)

    def _downLocChanged(self, state):
        self._ui.downButt.setEnabled(state)
        self._ui.downLoc.setEnabled(state)

    def _allowCacheChanged(self, state):
        self._ui.removeCache.setEnabled(state)
        self._ui.maxCacheLabel.setEnabled(state)
        self._ui.cacheMB.setEnabled(state)
        self._ui.storeCacheLabel.setEnabled(state)
        self._ui.cachePath.setEnabled(state)
        self._ui.changeCachePath.setEnabled(state)

    def _setManualProxyConfigurationEnabled(self, state):
        self._ui.proxyType.setEnabled(state)
        self._ui.proxyServer.setEnabled(state)
        self._ui.proxyPort.setEnabled(state)
        self._ui.proxyUsername.setEnabled(state)
        self._ui.proxyPassword.setEnabled(state)

    def _useExternalDownManagerChanged(self, state):
        self._ui.externalDownExecutable.setEnabled(state)
        self._ui.externalDownArguments.setEnabled(state)
        self._ui.chooseExternalDown.setEnabled(state)

    def _changeCachePathClicked(self):
        path = gVar.appTools.getExistingDirectory('Preferences-CachePath', self,
            _('Choose cache path...'), self._ui.cachePath.text())
        if not path:
            return

        self._ui.cachePath.setText(path)

    def _newTabChanged(self, value):
        self._ui.newTabFrame.setVisible(value == 3)

    def _afterLaunchChanged(self, value):
        self._ui.dontLoadTabsUntilSelected.setEnabled(value == 3 or value == 4)

    def _createProfile(self):
        name = QInputDialog.getText(self, _('New Profile'), _('Enter the new profile\'s name:'))
        name = gVar.appTools.filterCharsFromFilename(name)

        if not name:
            return

        res = ProfileManager.createProfile(name)

        if res == -1:
            QMessageBox.warning(self, _('Error!'), _('This profile already exists!'))
            return

        if res != 0:
            QMessageBox.warning(self, _('Error!'), _('Cannot create profile directory!'))
            return

        self._ui.startProfile.addItem(name)
        self._ui.startProfile.setCurrentIndex(self._ui.startProfile.count() - 1)

    def _deleteProfile(self):
        name = self._ui.startProfile.currentText()
        button = QMessageBox.warning(self, _('Confirmation'),
            _('Are you sure you want to permanently delete %s profile? This action cannot be undone!') % name,
            QMessageBox.Yes | QMessageBox.No
        )
        if button != QMessageBox.Yes:
            return

        ProfileManager.removeProfile(name)

        self._ui.startProfile.removeItem(self._ui.startProfile.currentIndex())

    def _startProfileIndexChanged(self, index):
        current = self._ui.startProfile.itemText(index) == ProfileManager.currentProfile()

        self._ui.deleteProfile.setEnabled(not current)
        self._ui.cannotDeleteActiveProfileLabel.setText(current and _('Note: You cannot delete active profile.') or '')

    def _setProgressBarColorIcon(self, color=QColor()):
        size = self.style().pixelMetric(QStyle.PM_ToolBarIconSize)
        pm = QPixmap(QSize(size, size))
        if not color.isValid():
            color = self.palette().color(QPalette.Highlight)
        pm.fill(color)
        self._ui.customColorToolButton.setIcon(QIcon(pm))
        self._ui.customColorToolButton.setProperty('ProgressColor', color)

    def _selectCustomProgressBarColor(self):
        color = self._ui.customColorToolButton.property('ProgressBar')
        if not color:
            color = QColor()
        newColor = QColorDialog.getColor(color, self, _('Select Color'))
        if newColor.isValid():
            self._setProgressBarColorIcon(newColor)

    def _showNotificationPreview(self):
        if self._ui.useOSDNotifications.isChecked():
            if self._notification:
                self._notifPosition = self._notification.pos()
                # TODO: del self._notification to close?
                self._notification = None
            self._notification = DesktopNotification(True)
            self._notification.setHeading(_('OSD Notification'))
            self._notification.setText(_('Drag it on the screen to place it where you want.'))
            self._notification.move(self._notifPosition)
            self._notification.show()
        elif self._ui.useNativeSystemNotifications.isChecked():
            gVar.app.desktopNotifications().nativeNotificationPreview()

    def _makeAppDefault(self):
        if const.OS_WIN:
            self._ui.checkNowDefaultBrowser.clicked.disconnect(self._makeAppDefault)
            self._ui.checkNowDefaultBrowser.setText(_('Default'))
            self._ui.checkNowDefaultBrowser.setEnabled(False)

            if not gVar.app.associationManager().showNativeDefaultAppSettingsUi():
                gVar.app.associationManager().registerAllAssociation()

    # private:
    # override
    def closeEvent(self, event):
        '''
        @param: event QCloseEvent
        '''
        settings = Settings()
        settings.beginGroup('Browser-View-Settings')
        settings.setValue('settingsDialogPage', self._ui.stackedWidget.currentIndex())
        settings.endGroup()

        settings.setValue('Preferences/Geometry', self.saveGeometry())
        event.accept()
