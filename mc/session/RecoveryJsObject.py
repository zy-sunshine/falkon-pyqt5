from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtProperty
from PyQt5.Qt import pyqtSlot
from mc.tools.IconProvider import IconProvider
from mc.common.globalvars import gVar
from mc.webtab.TabbedWebView import TabbedWebView

class RecoveryJsObject(QObject):
    def __init__(self, manager):
        '''
        @param: manager RestoreManager
        '''
        super().__init__()
        self._manager = manager  # RestoreManager
        self._page = None  # WebPage

    def setPage(self, page):
        '''
        @param: page WebPage
        '''
        assert(page)
        self._page = page

    def restoreData(self):
        '''
        @return: QJsonArray
        '''
        out = []
        idx = 0
        for window in self._manager.restoreData().windows:
            jdx = 0
            tabs = []
            for tab in window.tabs:
                icon = tab.icon.isNull() and IconProvider.emptyWebIcon() or tab.icon
                item = {}
                item['tab'] = jdx
                item['icon'] = gVar.appTools.pixmapToDataUrl(icon.pixmap(16))
                item['title'] = tab.title
                item['url'] = tab.url.toString()
                item['pinned'] = tab.isPinned
                item['current'] = window.currentTab == jdx
                tabs.append(item)
                jdx += 1
            window = {}
            window['window'] = idx
            idx += 1
            window['tabs'] = tabs
            out.append(window)
        return out

    restoreData = pyqtProperty(list, restoreData, constant=True)

    # public Q_SLOTS:
    @pyqtSlot()
    def startNewSession(self):
        self._closeTab()

        gVar.app.restoreManager().clearRestoreData()
        gVar.app.destroyRestoreManager()

    @pyqtSlot(list, list)
    def restoreSession(self, excludeWin, excludeTab):
        '''
        @param excludeWin QStringList
        @param excludeTab QStringList
        '''
        assert(len(excludeWin) == len(excludeTab))

        # This assumes that excludeWin and excludeTab are sorted in descending order

        # RestoreData
        data = self._manager.restoreData()

        for idx in range(len(excludeWin)):
            win = excludeWin[idx]
            tab = excludeTab[idx]

            if not gVar.appTools.containsIndex(data.windows, win) or \
                    gVar.appTools.containsIndex(data.windows[win].tabs, tab):
                continue

            wd = data.windows[win]

            wd.tabs.remove(tab)
            if wd.currentTab >= tab:
                wd.currentTab -= 1

            if not wd.tabs:
                data.windows.remove(win)
                continue

            if wd.currentTab < 0:
                wd.currentTab = len(wd.tabs) - 1

        if gVar.app.restoreSession(None, data):
            self._closeTab()
        else:
            self.startNewSession()

    # private:
    def _closeTab(self):
        # TabbedWebView
        view = self._page.view()
        if not isinstance(view, TabbedWebView):
            return

        if view.browserWindow().tabCount() > 1:
            view.closeView()
        else:
            view.browserWindow().close()
