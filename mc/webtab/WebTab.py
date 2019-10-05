from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.Qt import QVBoxLayout
from PyQt5.QtWidgets import QSplitter
from PyQt5.Qt import Qt
from PyQt5.Qt import QPalette
from PyQt5.Qt import QSizePolicy
from PyQt5.Qt import QByteArray
from PyQt5.Qt import QUrl
from PyQt5.Qt import QTimer
from PyQt5.Qt import QDataStream
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QLayout

from mc.webtab.TabbedWebView import TabbedWebView
from mc.webengine.WebPage import WebPage
from mc.webengine.WebInspector import WebInspector
from mc.navigation.LocationBar import LocationBar
from mc.tabwidget.TabIcon import TabIcon
from .SearchToolBar import SearchToolBar

class WebTab(QWidget):

    class SavedTab(object):
        def __init__(self, webTab=None):
            if webTab:
                self.setWebTab(webTab)
            else:
                self.title = ''
                self.url = QUrl()
                self.icon = QIcon()
                self.history = QByteArray()
                self.isPinned = False
                self.zoomLevel = False
                self.parentTab = -1
                self.childTabs = []
                self.sessionData = {}

        def setWebTab(self, webTab):
            self.title = webTab.title()
            self.url = webTab.url()
            self.icon = webTab.icon()
            self.history = webTab.historyData()
            self.isPinned = webTab.isPinned()
            self.zoomLevel = webTab.zoomLevel()
            if webTab.parentTab():
                self.parentTab = webTab.parentTab().tabIndex()
            else:
                self.parentTab = -1
            self.childTabs = webTab.childTabs()[:]
            self.sessionData = webTab.sessionData()

        def isValid(self):
            return not self.url.isEmpty() or not self.history.isEmpty()

        def clear(self):
            self.title.clear()
            self.url.clear()
            self.icon = QIcon()
            self.history.clear()
            self.isPinned = False
            self.zoomLevel = 1
            self.parentTab = -1
            self.childTabs.clear()
            self.sessionData.clear()

    # type AddChildBehavior
    AppendChild = 0
    PrependChild = 1

    s_addChildBehavior = AppendChild

    def __init__(self, parent=None):
        super(WebTab, self).__init__(parent)
        self.setObjectName('webtab')

        self._tabBar = None
        self._window = None
        self._parentTab = None
        self._childTabs = []
        self._sessionData = {}
        self._savedTab = self.SavedTab()
        self._isPinned = False
        self._isCurrentTab = False

        self._webView = TabbedWebView(self)
        self._webView.setPage(WebPage())
        self._webView.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setFocusProxy(self._webView)

        self._locationBar = LocationBar(self)
        self._locationBar.setWebView(self._webView)

        self._tabIcon = TabIcon(self)
        self._tabIcon.setWebTab(self)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._webView)

        viewWidget = QWidget(self)
        viewWidget.setLayout(self._layout)

        self._splitter = QSplitter(Qt.Vertical, self)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.addWidget(viewWidget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter)
        self.setLayout(layout)

        self._notificationWidget = QWidget(self)
        self._notificationWidget.setAutoFillBackground(True)
        pal = self._notificationWidget.palette()
        pal.setColor(QPalette.Window, pal.window().color().darker(110))
        self._notificationWidget.setPalette(pal)

        nlayout = QVBoxLayout(self._notificationWidget)
        nlayout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        nlayout.setContentsMargins(0, 0, 0, 0)
        nlayout.setSpacing(1)

        self._webView.showNotification.connect(self.showNotification)
        self._webView.loadFinished.connect(self.loadFinished)
        self._webView.titleChanged.connect(self.titleWasChanged)
        self._webView.titleChanged.connect(self.titleChanged)
        self._webView.iconChanged.connect(self.iconChanged)

        self._webView.backgroundActivityChanged.connect(self.backgroundActivityChanged)
        self._webView.loadStarted.connect(lambda: self.loadingChanged.emit(True))
        self._webView.loadFinished.connect(lambda: self.loadingChanged.emit(False))

        def pageChanged(page):
            page.audioMutedChanged.connect(self.playingChanged)
            page.recentlyAudibleChanged.connect(self.mutedChanged)

        pageChanged(self._webView.page())
        self._webView.pageChanged.connect(pageChanged)

        def tabIconResized():
            if self._tabBar:
                self._tabBar.update()
        self._tabIcon.resized.connect(tabIconResized)

    def browserWindow(self):
        '''
        @return BrowserWindow
        '''
        return self._window

    def webView(self):
        '''
        @return TabbedWebView
        '''
        return self._webView

    def locationBar(self):
        '''
        @return LocationBar
        '''
        return self._locationBar

    def tabIcon(self):
        '''
        @return TabIcon
        '''
        return self._tabIcon

    def parentTab(self):
        '''
        @return WebTab
        '''
        return self._parentTab

    def setParentTab(self, tab):
        if self._isPinned or self._parentTab == tab:
            return
        if tab and tab.isPinned():
            return

        if self._parentTab:
            index = self._parentTab._childTabs.index(self)
            if index >= 0:
                self._parentTab._childTabs.pop(index)
                self._parentTab.childTabRemoved.emit(self, index)
        self._parentTab = tab

        if tab:
            self._parentTab = None
            tab.addChildTab(self)
        else:
            self.parentTabChanged.emit(self._parentTab)

    def addChildTab(self, tab, index=-1):
        if self._isPinned or not tab or tab.isPinned():
            return

        oldParent = tab._parentTab
        tab._parentTab = self
        if oldParent:
            index = oldParent._childTabs.index(tab)
            if index >= 0:
                oldParent._childTabs.pop(index)
                oldParent.childTabRemoved.emit(tab, index)

        if index < 0 or index > len(self._childTabs):
            index = 0
            if self.addChildBehavior() == self.AppendChild:
                index = len(self._childTabs)
            else:  # PrependChild
                index = 0

        self._childTabs.insert(index, tab)
        self.childTabAdded.emit(tab, index)
        tab.parentTabChanged.emit(self)

    def childTabs(self):
        '''
        @return QVector<WebTab*>
        '''
        return self._childTabs

    def sessionData(self):
        '''
        @return {}
        '''
        return self._sessionData

    def setSessionData(self, key, value):
        self._sessionData[key] = value

    def url(self):
        if self.isRestored():
            if self._webView.url().isEmpty() and self._webView.isLoading():
                return self._webView.page().requestedUrl()
            return self._webView.url()
        else:
            return self._savedTab.url

    def title(self, allowEmpty=False):
        if self.isRestored():
            return self._webView.title(allowEmpty)
        else:
            return self._savedTab.title

    def icon(self, allowNull=False):
        if self.isRestored():
            return self._webView.icon(allowNull)
        if allowNull or not self._savedTab.icon.isNull():
            return self._savedTab.icon
        # TODO:
        #return IconProvider.emptyWebIcon()
        return None

    def history(self):
        '''
        @return QWebEngineHistory
        '''
        return self._webView.history()

    def zoomLevel(self):
        return self._webView.zoomLevel()

    def setZoomLevel(self, level):
        self._webView.setZoomLevel(level)

    def detach(self):
        assert(self._window)
        assert(self._tabBar)

        # Remove from tab tree
        self.removeFromTabTree()

        # Remove icon from tab
        self._tabBar.setTabButton(self.tabIndex(), self._tabBar.iconButtonPosition(), None)
        self._tabIcon.setParent(self)

        # Remove the tab from tabbar
        self._window.tabWidget().removeTab(self.tabIndex())
        self.setParent(None)
        # Remove the locationbar from window
        self._locationBar.setParent(self)
        # Detach TabbedWindow
        self._webView.setBrowserWindow(None)

        if self._isCurrentTab:
            self._isCurrentTab = False
            self.currentTabChanged.emit(self._isCurrentTab)

        self._tabBar.currentChanged.disconnect(self.onCurrentChanged)

        self._window = None
        self._tabBar = None

    def onCurrentChanged(self, index):
        wasCurrent = self._isCurrentTab
        self._isCurrentTab = index == self.tabIndex()
        if wasCurrent != self._isCurrentTab:
            self.currentTabChanged.emit(self._isCurrentTab)

    def attach(self, window):
        self._window = window
        self._tabBar = self._window.tabWidget().tabBar()

        self._webView.setBrowserWindow(self._window)
        self._locationBar.setBrowserWindow(self._window)
        self._tabBar.setTabText(self.tabIndex(), self.title())
        self._tabBar.setTabButton(self.tabIndex(), self._tabBar.iconButtonPosition(), self._tabIcon)
        QTimer.singleShot(0, self._tabIcon.updateIcon)

        self.onCurrentChanged(self._tabBar.currentIndex())
        self._tabBar.currentChanged.connect(self.onCurrentChanged)

    def historyData(self):
        '''
        @return QByteArray
        '''
        if self.isRestored():
            historyArray = QByteArray()
            stream = QDataStream(historyArray, QIODevice.WriteOnly)
            history = self._webView.history()
            stream << history
            return historyArray

    def stop(self):
        self._webView.stop()

    def reload(self):
        self._webView.reload()

    def load(self, request):
        '''
        @param: requset LoadRequest
        '''
        if self.isRestored():
            self.tabActivated()
            QTimer.singleShot(0, lambda: self.load(self, request))
        else:
            self._webView.load(request)

    def unload(self):
        self._savedTab = self.SavedTab(self)
        self.restoredChanged.emit(self.isRestored())
        self._webView.setPage(WebPage())
        self._webView.setFocus()

    def isLoading(self):
        return self._webView.isloading()

    def isPinned(self):
        return self._isPinned

    def setPinned(self, state):
        if self._isPinned == state:
            return
        if state:
            self.removeFromTabTree()
        self._isPinned = state
        self.pinnedChanged.emit(self._isPinned)

    def togglePinned(self):
        assert(self._tabBar)
        assert(self._window)
        self.setPinned(not self.isPinned())
        self._window.tabWidget().pinUnPinTab(self.tabIndex(), self.title())

    def isMuted(self):
        return self._webView.page().isAudioMuted()

    def isPlaying(self):
        return self._webView.page().recentlyAudible()

    def setMuted(self, muted):
        self._webView.page().setAudioMuted(muted)

    def toggleMuted(self):
        self.setMuted(not self.muted())

    def backgroundActivity(self):
        return self._webView.backgroundActivity()

    def tabIndex(self):
        index = -1
        if self._tabBar:
            index = self._tabBar.tabWidget().indexOf(self)
        return index

    def isCurrentTab(self):
        return self._isCurrentTab

    def makeCurrentTab(self):
        if self._tabBar:
            self._tabBar.tabWidget().setCurrentIndex(self.tabIndex())

    def closeTab(self):
        if self._tabBar:
            self._tabBar.tabWidget().closeTab(self.tabIndex())

    def moveTab(self, to):
        if self._tabBar:
            self._tabBar.tabWidget().moveTab(self.tabIndex(), to)

    def haveInspector(self):
        return self._splitter.count() > 1 and self._splitter.widget(1).inherits('WebInspector')

    def showWebInspector(self, inspectElement):
        if not WebInspector.isEnabled() or self.haveInspector():
            return

        inspector = WebInspector(self)
        inspector.setView(self._webView)
        if inspectElement:
            inspector.inspectElement()

        height = inspector.sizeHint().height()
        self._splitter.addWidget(inspector)
        self._splitter.setSizes((self._splitter.height() - height, height))

    def toggleWebInspector(self):
        if not self.haveInspector():
            self.showWebInspector()
        else:
            self._splitter.widget(1).destroy()  # TODO: del?

    def showSearchToolBar(self, searchText=''):
        index = 1
        toolBar = None
        if self._layout.count() == 1:
            toolBar = SearchToolBar(self._webView, self)
            self._layout.insertWidget(index, toolBar)
        if self._layout.count() == 2:
            assert(isinstance(self._layout.itemAt(index).widget(), SearchToolBar))
            toolBar = self._layout.itemAt(index).widget()
        assert(toolBar)
        if not searchText:
            toolBar.setText(searchText)
        toolBar.focusSearchLine()

    def isRestored(self):
        return not self._savedTab.isValid()

    def restoreTab(self, tab):
        '''
        @param: tab SavedTab
        '''
        assert(self._tabBar)
        self.setPinned(tab.isPinned())
        self._sessionData = tab._sessionData

        # TODO:
        if self.isPinned(): # and qzSettings->loadTabsOnActivation:
            self._savedTab = tab
            self.restoredChanged.emit(self.isRestored())
            index = self.tabIndex()
            self._tabBar.setTabText(index, tab.title)
            self._locationBar.showUrl(tab.url)
            self._tabIcon.updateIcon()
        else:
            # This is called only on restore session and restoring tabs
            # immediately crashes QtWebEngine, waiting after initialization is
            # complete fixes it
            QTimer.singleShot(1000, self, lambda: self.p_restoreTab(tab))

    def p_restoreTab(self, tab):
        '''
        @param: tab SavedTab
        '''
        self._p_restoreTabByUrl(tab.url, tab.history, tab.zoomLevel)

    def p_restoreTabByUrl(self, url, history, zoomLevel):
        self._webView.load(url)

        # Restoring history of internal pages crashes QtWebEngine 5.8
        blacklistedSchemes = ['view-source', 'chrome']

        if (url.scheme() not in blacklistedSchemes):
            stream = QDataStream(history)
            stream >> self._webView.history()

        self._webView.setZoomLevel(zoomLevel)
        self._webView.setFocus()

    def tabActivated(self):
        if self.isRestored():
            return

        def _onTabActivated():
            if self.isRestored():
                return
            self.p_restoreTab(self._savedTab)
            self._savedTab.clear()
            self.restoreChanged.emit(self.isRestored())

        QTimer.singleShot(0, self, _onTabActivated)

    def addChildBehavior(self):
        '''
        @return AddChildBehavior
        '''
        return self.s_addChildBehavior

    def setAddChildBehavior(self, behavior):
        self.s_addChildBehavior = behavior

    # Q_SLOTS
    @pyqtSlot(QWidget)
    def showNotification(self, notif):
        self._notificationWidget.setParent(self)
        self._notificationWidget.raise_()
        self._notificationWidget.setFixedWidth(self.width())
        self._notificationWidget.layout().addWidget(notif)
        self._notificationWidget.show()
        notif.show()

    @pyqtSlot()
    def loadFinished(self):
        self.titleWasChanged(self._webView.title())

    # Q_SIGNALS
    titleChanged = pyqtSignal(str) # title
    iconChanged = pyqtSignal(QIcon) # icon
    pinnedChanged = pyqtSignal(bool) # pinned
    restoredChanged = pyqtSignal(bool) # restored
    currentTabChanged = pyqtSignal(bool) # current
    loadingChanged = pyqtSignal(bool) # loading
    mutedChanged = pyqtSignal(bool) # muted
    playingChanged = pyqtSignal(bool) # playing
    backgroundActivityChanged = pyqtSignal(bool) # activity
    parentTabChanged = pyqtSignal('PyQt_PyObject') # WebTab*
    childTabAdded = pyqtSignal('PyQt_PyObject', int) # WebTab*, index
    childTabRemoved = pyqtSignal('PyQt_PyObject', int) # WebTab*, index

    def titleWasChanged(self, title):
        if not self._tabBar or not self._window or not title:
            return
        if self._isCurrentTab:
            self._window.setWindowTitle('%s - Demo' % title)
        self._tabBar.setTabText(self.tabIndex(), title)

    # override
    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        self._notificationWidget.setFixedWidth(self.width())

    def removeFromTabTree(self):
        parentTab = self._parentTab
        parentIndex = -1
        if parentTab:
            parentIndex = parentTab._childTabs.index(self)
        self.setParentTab(None)

        idx = 0
        while self._childTabs:
            child = self._childTabs[0]
            child.setParentTab(None)
            if parentTab:
                parentTab.addChildTab(child, parentIndex + idx)
                idx += 1
