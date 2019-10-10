from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import Qt
from PyQt5.Qt import QTimer
from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QRect
from PyQt5.Qt import QModelIndex
from mc.common.globalvars import gVar
from .LocationCompleterModel import LocationCompleterModel
from .LocationCompleterRefreshJob import LocationCompleterRefreshJob
from .LocationCompleterView import LocationCompleterView

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

        if not self._s_view:
            self._s_model = LocationCompleterModel()
            self._s_view = LocationCompleterView()
            self._s_view.setModel(self._s_model)

    def setMainWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._window = window

    def setLocationBar(self, locationBar):
        '''
        @param: locationBar LocationBar
        '''
        self._locationBar = locationBar

    def isVisible(self):
        return self._s_view.isVisible()

    def closePopup(self):
        self._s_view.close()

    # public Q_SLOTS:
    def complete(self, string):
        trimmedStr = string.strip()

        # Indicates that new completion was requested by user
        # Eg. popup was not closed yet this completion session
        self._popupClosed = False

        self.cancelRefreshJob.emit()

        job = LocationCompleterRefreshJob(trimmedStr)
        job.finished.connect(self._refreshJobFinished)
        self.cancelRefreshJob.connect(job.jobCancelled)

        if gVar.appSettings.searchFromAddressBar and \
                gVar.appSettings.showABSearchSuggestions and len(trimmedStr) >= 2:
            if not self._openSearchEngine:
                self._openSearchEngine = OpenSearchEngine(self)
                self._openSearchEngine.setNetworkAccessManager(gVar.app.networkManager())
                self._openSearchEngine.suggestions.connect(self._addSuggestions)
            from mc.navigation.LocationBar import LocationBar
            self._openSearchEngine.setSuggestionsUrl(LocationBar.searchEngine().suggestionsUrl)
            self._openSearchEngine.setSuggestionsParameters(LocationBar.searchEngine().suggestionsParameters)
            self._suggestionsTerm = trimmedStr
            self._openSearchEngine.requestSuggestions(self._suggestionsTerm)
        else:
            self._oldSuggestions.clear()

        # Add/update search/visit item
        def func():
            index = self._s_model.index(0, 0)
            if index.data(LocationCompleterModel.VisitSearchItemRole):
                self._s_model.setData(index, trimmedStr, Qt.DisplayRole)
                self._s_model.setData(index, trimmedStr, LocationCompleterModel.UrlRole)
                self._s_model.setData(index, self._locationBar.text(), LocationCompleterModel.SearchStringRole)
            else:
                item = QStandardItem()
                item.setText(trimmedStr)
                item.setData(trimmedStr, LocationCompleterModel.UrlRole)
                item.setData(self._locationBar.text(), LocationCompleterModel.SearchStringRole)
                item.setData(True, LocationCompleterModel.VisitSearchItemRole)
                self._s_model.setCompletions([item])
                self._addSuggestions(self._oldSuggestions)
            self._showPopup()
            if not self._s_view.currentIndex().isValid():
                self._ignoreCurrentChanged = True
                self._s_view.setCurrentIndex(self._s_model.index(0, 0))
                self._ignoreCurrentChanged = False
        QTimer.singleShot(0, func)

    def showMostVisited(self):
        self._locationBar.setFocus()
        self.complete('')

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
        job = self.sender()
        assert(isinstance(job, LocationCompleterRefreshJob))

        # Don't show results of older jobs
        # Also don't open the popup again when it was already closed
        if not job.isCanceled() and job.timestamp() > self._lastRefreshTimestamp and \
                not self._popupClosed:
            self._s_model.setCompletions(job.completions())
            self._addSuggestions(self._oldSuggestions)
            self._showPopup()

            self._lastRefreshTimestamp = job.timestamp()

            if not self._s_view.currentIndex().isValid() and \
                    self._s_model.index(0, 0).data(LocationCompleterModel.VisitSearchItemRole):
                self._ignoreCurrentChanged = True
                self._s_view.setCurrentIndex(self._s_model.index(0, 0))
                self._ignoreCurrentChanged = False

            if gVar.appSettings.useInlineCompletion:
                self.showDomainCompletion.emit(job.domainCompletion())

            self._s_model.setData(self._s_model.index(0, 0), self._locationBar.text(),
                    LocationCompleterModel.SearchStringRole)

        job.deleteLater()

    def _slotPopupClosed(self):
        self._popupClosed = True
        self._oldSuggestions.clear()

        self._s_view.closed.disconnect(self._slotPopupClosed)
        self._s_view.indexActivated.disconnect(self._indexActivated)
        self._s_view.indexCtrlActivated.disconnect(self._indexCtrlActivated)
        self._s_view.indexShiftActivated.disconnect(self._indexShiftActivated)
        self._s_view.indexDeleteRequested.disconnect(self._indexDeleteRequested)
        self._s_view.loadRequested.disconnect(self.loadRequested)
        self._s_view.searchEnginesDialogRequested.disconnect(self._openSearchEnginesDialog)
        self._s_view.selectionModel().currentChanged.disconnect(self._currentChanged)

        self.popupClosed.emit()

    def _addSuggestions(self, suggestions):
        '''
        @param: sugesstions QStringList
        '''
        suggestionItems = self._s_model.suggestionItems()

        # Delete existing suggestions
        for item in suggestionItems:
            self._s_model.takeRow(item.row())

        # Add new suggestions
        items = []  # QList<QStandardItem>
        for suggestion in suggestions:
            item = QStandardItem()
            item.setText(suggestion)
            item.setData(suggestion, LocationCompleterModel.TitleRole)
            item.setData(suggestion, LocationCompleterModel.UrlRole)
            item.setData(self._suggestionsTerm, LocationCompleterModel.SearchStringRole)
            item.setData(True, LocationCompleterModel.SearchSuggestionRole)
            items.append(item)
        self._s_model.addCompletions(items)
        self._oldSuggestions = suggestions

        if not self._popupClosed:
            self._showPopup()

    def _currentChanged(self, index):
        '''
        @param: index QModelIndex
        '''
        if self._ignoreCurrentChanged:
            return

        # QString
        completion = index.data()

        # Bool
        completeDomain = index.data(LocationCompleterModel.VisitSearchItemRole)

        originalText = self._s_model.index(0, 0).data(LocationCompleterModel.SearchStringRole)

        # Domain completion was dismissed
        if completeDomain and completion == originalText:
            completeDomain = False

        if not completion:
            completeDomain = True
            completion = originalText

        self.showCompletion.emit(completion, completeDomain)

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
        assert(self._window)
        assert(self._locationBar)

        if not self._locationBar.hasFocus() or self._s_model.rowCount() == 0:
            self._s_view.close()
            return

        if self._s_view.isVisible():
            self._adjustPopupSize()
            return

        popupRect = QRect(self._locationBar.mapToGlobal(self._locationBar.pos()),
                self._locationBar.size())
        popupRect.setY(popupRect.bottom())

        self._s_view.setGeometry(popupRect)
        self._s_view.setFocusProxy(self._locationBar)
        self._s_view.setCurrentIndex(QModelIndex())

        self._s_view.closed.connect(self._slotPopupClosed)
        self._s_view.indexActivated.connect(self._indexActivated)
        self._s_view.indexCtrlActivated.connect(self._indexCtrlActivated)
        self._s_view.indexShiftActivated.connect(self._indexShiftActivated)
        self._s_view.indexDeleteRequested.connect(self._indexDeleteRequested)
        self._s_view.loadRequested.connect(self.loadRequested)
        self._s_view.searchEnginesDialogRequested.connect(self._openSearchEnginesDialog)
        self._s_view.selectionModel().currentChanged.connect(self._currentChanged)

        #self._s_view.createWinId()
        self._s_view.winId()
        self._s_view.windowHandle().setTransientParent(self._window.windowHandle())

        self._adjustPopupSize()

    def _adjustPopupSize(self):
        self._s_view.adjustSize()
        self._s_view.show()
