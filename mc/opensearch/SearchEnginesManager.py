from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QIcon

class SearchEnginesManager(QObject):
    class Engine:
        def __init__(self):
            self.name = ''
            self.icon = QIcon()
            self.url = ''
            self.shortcut = ''

            self.sugesstionUrl = ''
            self.sugesstionsParameters = b''
            self.postData = b''

        def isValid(self):
            return self.name and self.url

        def __eq__(self, other):
            return self.name == other.name and \
                self.url == other.url and \
                self.sugesstionUrl == other.sugesstionUrl and \
                self.shortcut == other.shortcut

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settingsLoaded = False
        self._saveScheduled = False

        self._startingEngineName = ''
        self._defaultEngineName = ''
        self._allEngines = []  # QVector<Engine>
        self._activeEngine = self.Engine()
        self._defaultEngine = self.Engine()

    def searchResult(self, engine, string):
        '''
        @param: engine Engine
        @param: string QString
        '''
        pass

    def searchResultWithDefaultEngine(self, string):
        pass

    def addEngineWithUrl(self, url):
        '''
        @param: url QUrl
        '''
        pass

    def addEngineWithOpenSearchEngine(self, engine):
        '''
        @param: engine OpenSearchEngine
        '''
        pass

    def addEngine(self, engine):
        '''
        @param: Engine
        '''
        pass

    def addEngineFromForm(self, formData, view):
        '''
        @param: formData QVariantMap
        @param: view WebView
        '''

    def removeEngine(self, engine):
        '''
        @param: engine Engine
        '''
        pass

    def setActiveEngine(self, engine):
        '''
        @param: engine Engine
        '''
        pass

    def activeEngine(self):
        '''
        @return: Engine
        '''
        return self._activeEngine

    def setDefaultEngine(self, engine):
        '''
        @param: engine Engine
        '''
        pass

    def defaultEngine(self):
        '''
        @return Engine
        '''
        return self._defaultEngine

    def editEngine(self, before, after):
        '''
        @param: before Engine
        @param: after Engine
        '''
        pass

    def engineForShortcut(self, shortcut):
        '''
        @param: shortcut QString
        @return: Engine
        '''
        pass

    def setAllEngines(self, engines):
        '''
        @param: engines QVector<Engine>
        '''
        self._allEngines = engines
        self.enginesChanged.emit()

    def allEngines(self):
        '''
        @return: QVector<Engine>
        '''
        return self._allEngines

    def startingEngineName(self):
        '''
        @return: QString
        '''
        return self._startingEngineName

    def saveSettings(self):
        pass

    def restoreDefaults(self):
        pass

    @classmethod
    def iconForSearchEngine(cls, url):
        '''
        @param: url QUrl
        @return: QIcon
        '''
        pass

    # Q_SIGNALS:
    enginesChanged = pyqtSignal()
    activeEngineChanged = pyqtSignal()
    defaultEngineChanged = pyqtSignal()

    # private Q_SLOTS:
    def _engineChangedImage(self):
        pass

    def _replyFinished(self):
        pass

    def _scheduleSave(self):
        self._saveScheduled = True

    # private:
    def _checkEngine(self, engine):
        '''
        @param: engine OpenSearchEngine
        '''
        pass

    def _loadSettings(self):
        pass

SearchEngine = SearchEnginesManager.Engine
