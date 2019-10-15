from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import pyqtProperty
from PyQt5.Qt import QNetworkAccessManager
from PyQt5.Qt import QImage
from PyQt5.Qt import QByteArray

class OpenSearchEngine(QObject):
    # Q_SIGNALS:
    imageChanged = pyqtSignal()
    suggestions = pyqtSignal([])  # suggestions

    # typedef QPair<QString, QString> Parameter
    # typedef QList<Parameter> Parameters
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = ''
        self._description = ''

        self._imageUrl = ''
        self._image = QImage()

        self._searchUrlTemplate = ''
        self._suggestionsUrlTemplate = ''
        self._searchParameters = []  # QList<Parameter>
        self._suggestionsParameters = []  # QList<Parameter>
        self._searchMethod = ''
        self._suggestionsMethod = ''

        self._preparedSuggestionsParameters = QByteArray()
        self._preparedSuggestionsUrl = ''

        self._requestMethods = {}  # QMap<QString, QNetworkAccessManager::Operation>

        self._networkAccessManager = None  # QNetworkAccessManager
        self._suggestionsReply = None  # QNetworkReply

        self._delegate = None  # OpenSearchEngineDelegate

    # public:
    def name(self):
        '''
        @return: QString
        '''
        pass

    def setName(self, name):
        '''
        @param: name QString
        '''
        pass

    def description(self):
        '''
        @return: QString
        '''
        pass

    def setDescription(self, description):
        '''
        @param: description QString
        '''
        pass

    def searchUrlTemplate(self):
        '''
        @return: QString
        '''
        pass

    def setSearchUrlTemplate(self, searchUrl):
        '''
        @param: searchUrl QString
        '''
        pass

    def searchUrl(self, searchTerm):
        '''
        @param: searchTerm QString
        @return: QUrl
        '''
        pass

    def getPostData(self, searchTerm):
        '''
        @param: searchTerm QString
        @return: QByteArray
        '''
        pass

    def providesSuggestions(self):
        '''
        @return: bool
        '''
        pass

    def suggestionsUrlTemplate(self):
        '''
        @return: QString
        '''
        pass

    def setSuggestionsUrlTemplate(self, suggestionsUrl):
        '''
        @param: suggestionsUrl QString
        '''
        pass

    def suggestionsUrl(self, searchTerm):
        '''
        @param: searchTerm QString
        '''
        pass

    def searchParameters(self):
        '''
        @return: QList<Parameter> (which Parameter is QList<QString, QString>)
        '''
        pass

    def setSearchParameters(self, searchParameters):
        '''
        @param: searchParameters QList<Parameter> (which Parameter is QList<QString, QString>)
        '''
        pass

    def suggestionsParameters(self):
        '''
        @return: QList<Parameter>
        '''
        pass

    def setSuggestionsParameters(self, suggestionsParameters):
        '''
        @param: suggestionsParameters QList<Parameter>
        '''
        pass

    def searchMethod(self):
        '''
        @return: QString
        '''
        pass

    def setSearchMethod(self, method):
        '''
        @param: method QString
        '''
        pass

    def suggestionsMethod(self):
        '''
        @return: QString
        '''
        pass

    def setSuggestionsMethod(self, method):
        '''
        @param: method QString
        '''
        pass

    def imageUrl(self):
        '''
        @return: QString
        '''
        pass

    def setImageUrl(self, url):
        '''
        @param: url QString
        '''
        pass

    def image(self):
        '''
        @return: QImage
        '''
        pass

    def setImage(self, image):
        '''
        @param: image QImage
        '''
        pass

    def isValid(self):
        '''
        @return: bool
        '''
        pass

    def setSuggestionsUrl(self, string):
        '''
        @param: string QString
        '''
        pass

    def setSuggestionsParametersByBytes(self, parameters):
        '''
        @param: parameters QByteArray
        '''
        pass

    def getSuggestionsUrl(self):
        '''
        @return: QString
        '''
        pass

    def getSuggestionsParameters(self):
        '''
        @return: QByteArray
        '''
        pass

    def networkAccessManager(self):
        '''
        @return: QNetworkAccessManager
        '''
        pass

    def setNetworkAccessManager(self, networkAccessManager):
        '''
        @param: networkAccessManager QNetworkAccessManager
        '''
        pass

    def delegate(self):
        '''
        @return: OpenSearchEngineDelegate
        '''
        pass

    def setDelegate(self, delegate):
        '''
        @param: delegate OpenSearchEngineDelegate
        '''
        pass

    def __eq__(self, other):
        pass

    def __lt__(self, other):
        pass

    # public Q_SLOTS:
    def requestSuggestions(self, searchTerm):
        '''
        @param: searchTerm QString
        '''
        pass

    def requestSearchResults(self, searchTerm):
        '''
        @param: searchTerm QString
        '''
        pass

    name = pyqtProperty(str, name, setName)
    description = pyqtProperty(str, description, setDescription)
    searchUrlTemplate = pyqtProperty(str, searchUrlTemplate, setSearchUrlTemplate)
    searchParameters = pyqtProperty(list, searchParameters, setSearchParameters)
    searchMethod = pyqtProperty(str, searchMethod, setSearchMethod)
    suggestionsUrlTemplate = pyqtProperty(str, suggestionsUrlTemplate, setSuggestionsUrlTemplate)
    suggestionsParameters = pyqtProperty(list, suggestionsParameters, setSuggestionsParameters)
    suggestionsMethod = pyqtProperty(str, suggestionsMethod, setSuggestionsMethod)
    providesSuggestions = pyqtProperty(bool, providesSuggestions)
    imageUrl = pyqtProperty(str, imageUrl, setImageUrl)
    valid = pyqtProperty(bool, isValid)
    networkAccessManager = pyqtProperty(QNetworkAccessManager, networkAccessManager, setNetworkAccessManager)

    # protected:
    @staticmethod
    def _parseTemplate(cls, searchTerm, searchTemplate):
        pass

    def _loadImage(self):
        pass

    # private Q_SLOTS:
    def _imageObtained(self):
        pass

    def _suggestionsObtained(self):
        pass
