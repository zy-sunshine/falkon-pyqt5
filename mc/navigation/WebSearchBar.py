from PyQt5.QtWidgets import QLineEdit
from mc.tools.ClickableLabel import ClickableLabel

class LineEdit(QLineEdit):
    pass

class WebSearchBar_Button(ClickableLabel):
    def __init__(self, parent=0):
        super().__init__(parent)

    # private:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass

class WebSearchBar(LineEdit):
    def __init__(self, window):
        super().__init__()
        self._window = window

        self._completer = None  # QCompleter
        self._completerModel = None  # QStringListModel
        self._openSearchEngine = None  # OpenSearchEngine
        # TODO:
        # self._activeEngine = SearchEngine()

        self._buttonSearch = None  # WebSearchBar_button
        self._boxSearchType = None  # ButtonWithMenu
        self._searchManager = None  # SearchEnginesManager
        self._searchDialog = None  # QPointer<SearchEnginesDialog>

        self._reloadingEngines = False

    # private Q_SLOTS:
    def _searchChanged(self, item):
        '''
        @param: item ButtonWithItem::Item
        '''
        pass

    def _setupEngines(self):
        pass

    def _search(self):
        pass

    def _searchInNewTab(self):
        pass

    def _aboutToShowMenu(self):
        pass

    def _openSearchEnginesDialog(self):
        pass

    def _enableSearchSuggestions(self, enable):
        pass

    def _addSuggestions(self, suggestions):
        '''
        @params: suggestions QStringList
        '''
        pass

    def _addEngineFromAction(self):
        pass

    def _pasteAndGo(self):
        pass

    def _instantSearchChanged(self, changed):
        pass

    # private:
    def focusOutEvent(self, event):
        '''
        @param: event QFocusEvent
        '''
        pass

    def dropEvent(self, event):
        '''
        @param: event QDropEvent
        '''
        pass

    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        pass

    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        pass
