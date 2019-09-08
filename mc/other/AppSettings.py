from mc.common import const

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
        self.loadtabsOnActivation = False

        self.autoOpenProtocols = []  # QStringList
        self.blockedProtocols = []  # QStringList

        # Browser-Tabs-Settings
        self.newTabPosition = const.NT_NewEmptyTab  # const.NewTablPositioinFlags
        self.tabsOnTop = False
        self.openPopupsInTabs = False
        self.alwaysSwitchTabsWithWheel = False

    def loadSettings(self):
        pass

    def saveSettings(self):
        pass
