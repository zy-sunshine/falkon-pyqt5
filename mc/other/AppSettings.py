from mc.common import const
from mc.app.Settings import Settings
from mc.webengine.WebView import WebView

class AppSettings:
    def __init__(self):
        # AddressBar
        self.selectAllOnDoubleClick = False
        self.selectAllOnClick = False
        self.showLoadingProgress = True
        self.showLocationSuggestions = 0
        self.showSwitchTab = False
        self.alwaysShowGoIcon = False
        self.useInlineCompletion = False

        # SearchEngines
        self.searchOnEngineChange = False
        self.searchFromAddressBar = False
        self.searchWithDefaultEngine = False
        self.showABSearchSuggestions = False
        self.showWSBSearchSuggestions = False

        # Web-Browser-Settings
        self.defaultZoomLevel = 0
        self.loadTabsOnActivation = False

        self.autoOpenProtocols = []  # QStringList
        self.blockedProtocols = []  # QStringList

        # Browser-Tabs-Settings
        self.newTabPosition = const.NT_NewEmptyTab  # const.NewTablPositioinFlags
        self.tabsOnTop = False
        self.openPopupsInTabs = False
        self.alwaysSwitchTabsWithWheel = False

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('AddressBar')
        self.selectAllOnDoubleClick = settings.value('SelectAllTextOnDoubleClick', True)
        self.selectAllOnClick = settings.value('SelectAllTextOnClick', False)
        self.showLoadingProgress = settings.value('ShowLoadingProgress', True)
        self.showLocationSuggestions = settings.value('showSuggestions', 0)
        self.showSwitchTab = settings.value('showSwitchTab', True)
        self.alwaysShowGoIcon = settings.value('alwaysShowGoIcon', False)
        self.useInlineCompletion = settings.value('useInlineCompletion', True)
        settings.endGroup()

        settings.beginGroup('SearchEngines')
        self.searchOnEngineChange = settings.value('SearchOnEngineChange', True)
        self.searchFromAddressBar = settings.value('SearchFromAddressBar', True)
        self.searchWithDefaultEngine = settings.value('SearchWithDefaultEngine', False)
        self.showABSearchSuggestions = settings.value('showSearchSuggestions', True)
        self.showWSBSearchSuggestions = settings.value('showSuggestions', True)
        settings.endGroup()

        settings.beginGroup('Web-Browser-Settings')
        self.defaultZoomLevel = settings.value('DefaultZoomLevel', WebView.zoomLevels().index(100), type=int)
        self.loadTabsOnActivation = settings.value('LoadTabsOnActivation', True)
        self.autoOpenProtocols = settings.value('AutomaticallyOpenProtocols', [])
        self.blockedProtocols = settings.value('BlockOpeningProtocols', [])
        settings.endGroup()

        settings.beginGroup('Browser-Tabs-Settings')
        if settings.value('OpenNewTabsSelected', False):
            self.newTabPosition = const.NT_CleanSelectedTab
        else:
            self.newTabPosition = const.NT_CleanNotSelectedTab
        self.tabsOnTop = settings.value('TabsOnTop', True)
        self.openPopupsInTabs = settings.value('OpenPopupsInTabs', False)
        self.alwaysSwitchTabsWithWheel = settings.value('AlwaysSwitchTabsWithWheel', False)
        settings.endGroup()

    def saveSettings(self):
        settings = Settings()
        settings.beginGroup('Web-Browser-Settings')
        settings.setValue('AutomaticallyOpenProtocols', self.autoOpenProtocols)
        settings.setValue('BlockOpeningProtocols', self.blockedProtocols)
        settings.endGroup()

        settings.beginGroup('Browser-Tabs-Settings')
        settings.setValue('TabsOnTop', self.tabsOnTop)
        settings.endGroup()
