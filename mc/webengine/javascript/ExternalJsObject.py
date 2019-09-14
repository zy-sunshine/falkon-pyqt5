from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtProperty
from .AutoFillJsObject import AutoFillJsObject
from mc.common.globalvars import gVar

class ExternalJsObject(QObject):
    _s_extraObjects = {}  # QHash<QString, QObject>
    def __init__(self, page):
        '''
        @param: page WebPage
        '''
        super().__init__(page)
        self._page = page  # WebPage
        self._autoFill = None  # AutoFillJsObject

        self._autoFill = AutoFillJsObject(self)

    def page(self):
        '''
        @return: WebPage
        '''
        return self._page

    @classmethod
    def setupWebChannel(cls, webChannel, page):
        '''
        @param: webChannel QWebChannel
        @param: page WebPage
        '''
        webChannel.registerObject('app_object', ExternalJsObject(page))

        for key, val in cls._s_extraObjects.items():
            webChannel.registerObject('app_' + key, val)

    @classmethod
    def registerExtraObject(cls, id_, object_):
        '''
        @param: id_ QString
        @param: object_ QObject
        '''
        cls._s_extraObjects[id_] = object_

    @classmethod
    def unregisterExtraObject(cls, object_):
        '''
        @param: object_ QObject
        '''
        removeKey = None
        for key, val in cls._s_extraObjects.items():
            if val == object_:
                removeKey = key
                break

        if removeKey is not None:
            cls._s_extraObjects.pop(removeKey)

    # private:
    def _speedDial(self):
        '''
        @return: QObject
        '''
        if self._page.url().toString() != 'app:speeddial':
            return None

        return gVar.app.plugins().speedDial()

    speedDial = pyqtProperty(QObject, _speedDial)

    def _autoFill(self):
        '''
        @return: QObject
        '''
        return self._autoFill

    autoFill = pyqtProperty(QObject, _autoFill)

    def _recovery(self):
        '''
        @return: QObject
        '''
        if not gVar.app.restoreManager() or self._page.url().toString() != 'app:restore':
            return None

        return gVar.app.restoreManager().recoveryObject(self._page)

    recovery = pyqtProperty(QObject, _recovery)
