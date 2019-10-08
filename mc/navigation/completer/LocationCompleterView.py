from PyQt5.Qt import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QModelIndex
from mc.webengine.LoadRequest import LoadRequest

class LocationCompleterView(QWidget):
    def __init__(self):
        super().__init__(None)
        self._view = None  # QListView
        self._delegate = None  # LocationCompleterDelegate
        self._searchEnginesLayout = None  # QHBoxLayout
        self._resizeHeight = -1
        self._resizeTimer = None  # QTimer
        self._forceResize = True

    def model(self):
        '''
        @return: QAbstractItemModel
        '''
        pass

    def setModel(self, model):
        '''
        @param model QAbstractItemModel
        '''
        pass

    def selectionModel(self):
        '''
        @return: QItemSelectionModel
        '''
        pass

    def currentIndex(self):
        '''
        @return: QModelIndex
        '''
        pass

    def setCurrentIndex(self, index):
        '''
        @param index QModelIndex
        '''
        pass

    def adjustSize(self):
        pass

    # override
    def eventFilter(self, obj, event):
        '''
        @param obj QObject
        @param event QEvent
        @return: bool
        '''
        pass

    # Q_SIGNALS
    closed = pyqtSignal()
    searchEnginesDialogRequested = pyqtSignal()
    loadRequested = pyqtSignal(LoadRequest)

    indexActivated = pyqtSignal(QModelIndex)
    indexCtrlActivated = pyqtSignal(QModelIndex)
    indexShiftActivated = pyqtSignal(QModelIndex)
    indexDeleteRequested = pyqtSignal(QModelIndex)

    # public Q_SLOTS:
    def close(self):
        pass

    # private:
    def _setupSearchEngines(self):
        pass

    def _openSearchEnginesDialog(self):
        pass
