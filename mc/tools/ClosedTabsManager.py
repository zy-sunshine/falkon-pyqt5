from mc.webtab.WebTab import WebTab
class ClosedTabsManager(object):

    class Tab:
        def __init__(self):
            self.position = -1
            self.parentTab = None  # QPointer<WebTab>
            self.tabState = WebTab.SavedTab()

        def isValid(self):
            return self.position > -1

    def __init__(self):
        self._closedTabs = []  # QVector<Tab>

    def saveTab(self, tab):
        pass

    def isClosedTabAvailable(self):
        return len(self._closedTabs) > 0

    def takeLastClosedTab(self):
        '''
        @brief: Takes tab that was most recently closed
        '''
        pass

    def takeTabAt(self, index):
        '''
        @brief: Takes tab at given index
        '''
        pass

    def closedTabs(self):
        '''
        @return: QVector<Tab>
        '''
        pass

    def clearClosedTabs():
        pass
