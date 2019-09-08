from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal

class LocationCompleter(QObject):
    _s_view = None  # LocationCompleterView
    _s_model = None  # LocationCompleterModel
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window = None  # BrowserWindow
        self._locationBar = None  # LocationBar
        self._lastRefreshTimestamp = 0  # qint64
        self._popupClosed = False
        self._ignoreCurrentChanged = False
        self._openSearchEngine = None  # OpenSearchEngine
        self._oldSuggestions = []  # QStringList
        self._suggestionsTerm = ''

    def setMainWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        pass

    def setLocationBar(self, locationBar):
        '''
        @param: locationBar LocationBar
        '''
        pass

    def isVisible(self):
        pass

    def closePopup(self):
        pass

    # public Q_SLOTS:
    def complete(self, string):
        pass

    def showMostVisited(self):
        pass

    # Q_SIGNALS:
    # QString completion, bool completeDomain
    showCompletion = pyqtSignal(str, bool)
    # QString completion
    showDomainCompletion = pyqtSignal(str)
    clearCompletion = pyqtSignal()
    popupClosed = pyqtSignal()
    cancelRefreshJob = pyqtSignal()
    # LoadRequest request
    loadRequested = pyqtSignal('PyQt_PyObject')

    # private Q_SLOTS
    def _refreshJobFinished(self):
        pass

    def _slotPopupClosed(self):
        pass

    def _addSuggestions(self, suggestions):
        '''
        @param: sugesstions QStringList
        '''
        pass

    def _currentChanged(self, index):
        '''
        @param: index QModelIndex
        '''
        pass

    def _indexActivated(self, index):
        '''
        @param: index QModelIndex
        '''
        pass

    def _indexCtrlActivated(self, index):
        '''
        @param: index QModelIndex
        '''
        pass

    def _indexShiftActivated(self, index):
        '''
        @param: index QModelIndex
        '''
        pass

    def _indexDeleteRequested(self, index):
        '''
        @param: index QModelIndex
        '''
        pass

    # private
    def _createLoadRequest(self, index):
        '''
        @param: index QModelIndex
        @return: LoadRequest
        '''
        pass

    def _switchToTab(self, window, tab):
        '''
        @param: window BrowserWindow
        @param: tab int
        '''
        pass

    def _loadRequest(self, request):
        '''
        @param: request LoadRequest
        '''
        pass

    def _openSearchEnginesDialog(self):
        pass

    def _showPopup(self):
        pass

    def _adjustPopupSize(self):
        pass
