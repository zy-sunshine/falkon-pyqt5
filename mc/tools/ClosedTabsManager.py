from mc.webtab.WebTab import WebTab
from mc.common.globalvars import gVar

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
        '''
        @param: tab WebTab
        '''
        if gVar.app.isPrivate():
            return

        # Don't save empty tab
        if tab.url().isEmpty() and len(tab.history().items()) == 0:
            return

        closedTab = self.Tab()
        closedTab.position = tab.tabIndex()
        closedTab.parentTab = tab.parentTab()
        closedTab.tabState = WebTab.SavedTab(tab)
        self._closedTabs.insert(0, closedTab)

    def isClosedTabAvailable(self):
        return len(self._closedTabs) > 0

    def takeLastClosedTab(self):
        '''
        @brief: Takes tab that was most recently closed
        '''
        tab = self.Tab()
        if self._closedTabs:
            tab = self._closedTabs.pop(0)
        return tab

    def takeTabAt(self, index):
        '''
        @brief: Takes tab at given index
        '''
        tab = self.Tab()
        if gVar.appTools.containsIndex(self._closedTabs, index):
            tab = self._closedTabs.pop(index)
        return tab

    def closedTabs(self):
        '''
        @return: QVector<Tab>
        '''
        return self._closedTabs[:]

    def clearClosedTabs(self):
        self._closedTabs.clear()
