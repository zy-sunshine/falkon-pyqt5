from PyQt5.Qt import QObject

class AutoFillJsObject(QObject):
    def __init__(self, parent):
        '''
        @param: parent ExternalJsObject
        '''
        super().__init__(parent)
        self._jsObject = None  # ExternalJsObject

    # public Q_SLOTS:
    def formSubmitted(self, frameUrl, username, password, data):
        '''
        @param: frameUrl QString
        @param: username QString
        @param: password QString
        @param: data QByteArray
        '''
        pass
