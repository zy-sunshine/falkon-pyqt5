from mc.tools.EnhancedMenu import Menu
from mc.tools.IconProvider import IconProvider
from PyQt5.Qt import QStyle
from mc.common.globalvars import gVar
from PyQt5.Qt import Qt
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QIcon
from mc.common import const
from mc.tools.EnhancedMenu import Action

class HistoryMenu(Menu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window = None  # QPointer<BrowserWindow>
        self._menuMostVisited = None  # Menu
        self._menuClosedTabs = None  # Menu
        self._menuClosedWindows = None  # Menu
        self._init()

    def setMainWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._window = window

    # private Q_SLOTS:
    def _goBack(self):
        if self._window:
            self._window.goBack()

    def _goForward(self):
        if self._window:
            self._window.goForward()

    def _goHome(self):
        if self._window:
            self._window.goHome()

    def _showHistoryManager(self):
        if self._window:
            self._window.showHistoryManager()

    def _aboutToShow(self):
        # Set enabled states for Back/Forward actions according to current WebView
        # TabbedWebView view
        view = None
        if self._window:
            view = self._window.weView()
        if view:
            self.actions()[0].setEnabled(view.history().canGoBack())
            self.actions()[1].setEnabled(view.history().canGoForward())

        while len(self.actions()) != 8:
            act = self.actions()[8]
            if act.menu():
                act.menu().clear()
            self.removeAction(act)
            del act

        self.addSeparator()

        # TODO:
        '''
        QSqlQuery query(SqlDatabase::instance()->database());
        query.exec(QSL("SELECT title, url FROM history ORDER BY date DESC LIMIT 10"));

        while (query.next()) {
            const QUrl url = query.value(1).toUrl();
            const QString title = QzTools::truncatedText(query.value(0).toString(), 40);

            Action* act = new Action(title);
            act->setData(url);
            act->setIcon(IconProvider::iconForUrl(url));
            connect(act, &QAction::triggered, this, &HistoryMenu::historyEntryActivated);
            connect(act, &Action::ctrlTriggered, this, &HistoryMenu::historyEntryCtrlActivated);
            connect(act, &Action::shiftTriggered, this, &HistoryMenu::historyEntryShiftActivated);
            addAction(act);
        }
        '''

    def _aboutToHide(self):
        # Enable Back/Forward actions to ensure shortcuts are working
        self.actions()[0].setEnabled(True)
        self.actions()[1].setEnabled(True)

    def _aboutToShowMostVisited(self):
        self._menuMostVisited.clear()

        mostVisited = gVar.app.history().mostVisited(10)
        for entry in mostVisited:
            act = Action(gVar.appTools.truncatedText(entry.title, 40))
            act.setData(entry.url)
            act.setIcon(IconProvider.iconForUrl(entry.url))
            act.triggered(self._historyEntryActivated)
            act.ctrlTriggered(self._historyEntryCtrlActivated)
            act.shiftTriggered(self._historyEntryShiftActivated)
            self._menuMostVisited.addAction(act)

        if self._menuMostVisited.isEmpty():
            self._menuMostVisited.addAction('Empty').setEnabled(False)

    def _aboutToShowClosedTabs(self):
        pass

    def _aboutToShowClosedWindows(self):
        pass

    def _historyEntryActivated(self):
        pass

    def _historyEntryCtrlActivated(self):
        pass

    def _historyEntryShiftActivated(self):
        pass

    def _openUrl(self, url):
        '''
        @param: url QUrl
        '''
        if self._window:
            self._window.loadAddress(url)

    def _openUrlInNewTab(self, url):
        '''
        @param: url QUrl
        '''
        if self._window:
            self._window.tabWidget().addViewByUrl(url, gVar.appSettings.newTabPosition)

    def _openUrlInNewWindow(self, url):
        '''
        @param: url QUrl
        '''
        gVar.app.createWindow(const.BW_NewWindow, url)

    # private:
    def _init(self):
        self.setTitle('Hi&story')

        icon = IconProvider.standardIcon(QStyle.SP_ArrowBack)
        act = self.addAction(icon, '&Back', self._goBack)
        act.setShortcut(gVar.appTools.actionShortcut(QKeySequence.Back,
            Qt.ALT + Qt.Key_Left, QKeySequence.Forward, Qt.ALT + Qt.Key_Right))

        icon = IconProvider.standardIcon(QStyle.SP_ArrowForward)
        act = self.addAction(icon, '&Forward', self._goForward)
        act.setShortcut(gVar.appTools.actionShortcut(QKeySequence.Forward,
            Qt.ALT + Qt.Key_Right, QKeySequence.Back, Qt.ALT + Qt.Key_Left))

        act = self.addAction(QIcon.fromTheme('go-home'), '&Home', self._goHome)
        act.setShortcut(QKeySequence(Qt.ALT + Qt.Key_Home))

        icon = QIcon.fromTheme('deep-history', QIcon(':/icons/menu/history.svg'))
        act = self.addAction(icon, 'Show &All History', self._showHistoryManager)
        act.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_H))

        self.addSeparator()

        self.aboutToShow.connect(self._aboutToHide)
        self.aboutToHide.connect(self._aboutToShow)

        self._menuMostVisited = Menu('Most Visited', self)
        self._menuMostVisited.aboutToShow.connect(self._aboutToShowMostVisited)

        self._menuClosedTabs = Menu('Closed Tabs')
        self._menuClosedTabs.aboutToShow.connect(self._aboutToShowClosedTabs)

        self._menuClosedWindows = Menu('Closed Windows')
        self._menuClosedWindows.aboutToShow.connect(self._aboutToShowClosedWindows)

        self.addMenu(self._menuMostVisited)
        self.addMenu(self._menuClosedTabs)
        self.addMenu(self._menuClosedWindows)
