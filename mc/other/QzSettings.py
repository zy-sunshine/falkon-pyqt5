from mc.common.designutil import Singleton

class QzSettings(Singleton):
    def __init__(self):
        # AddressBar
        self.selectAllOnDoubleClick = False
        self.selectAllOnClick = False
        self.showLoadingProgress = False
        self.showLocationSuggestions = 0
        self.showSwitchTab = False
        self.alwaysShowGoIcon = False
        self.useInlineCompletion = False

        # SearchEngines
        self.searchOnEngineChange = False
        self.searchFromAddressBar = False
        self.searchWithDefaultEngine = False
        self.showABSearchSuggestion = False
        self.showWSSearchSuggestion = False

        # Web-Browser-Settings
        self.defaultZoomLevel = 0
        self.loadTabsOnActivation = False

        self.autoOpenProtocols = []  # QStringList
        self.blockedProtocols = []  # QStringList

        # Browser-Tabs-Settings
        self.newTabPosition = 0  # Qz::NewTabPositionFlags
        self.tabsOnTop = False
        self.openPopupsInTabs = False
        self.alwaysSwitchTabsWithWheel = False

    def loadSettings(self):
        pass

    def saveSettings(self):
        pass
