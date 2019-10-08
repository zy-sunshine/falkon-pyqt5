from PyQt5.Qt import QObject

class LocationCompleterRefreshJob(QObject):
    def __init__(self, searchString):
        self._timestamp = 0  # qint64
        self._searchString = ''
        self._domainCompletion = ''
        self._items = []  # QList<QStandardItem>
        self._watcher = None  # QFutureWatcher<void>*
        self._jobCancelled = False

    def timestamp(self):
        '''
        @brief: Timestamp when the job has create
        @return: qint64
        '''
        pass

    def searchString(self):
        '''
        @return: QString
        '''
        pass

    def isCanceled(self):
        '''
        @return: bool
        '''
        pass

    def completions(self):
        '''
        @return: QList<QStandardItem>
        '''
        pass

        def domainCompletion(self):
        '''
        @return: QString
        '''
        pass

    # Q_SIGNALS
    finished = pyqtSignal()

    # private Q_SLOTS:
    def _slotFinished(self):
        pass

    def __jobCancelled(self):
        pass

    # private:
    # enum Type
    HistoryAndBookmarks = 0
    History = 1
    Bookmarks = 2
    Nothing = 4

    def _runJob(self):
        pass

    def _completeFromHistory(self):
        pass

    def _completeMostVisited(self):
        pass

    def createDomainCompletion(self, completion):
        '''
        @param completion QString
        @return: QString
        '''
        pass
