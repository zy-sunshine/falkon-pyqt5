from PyQt5.QtWidgets import QStatusBar

class StatusBar(QStatusBar):

    class WidgetData:
        def __init__(self):
            self.id = ''
            self.widget = None  # QWidget
            self.button = None  # AbstractButtonInterface

    def __init__(self, window):
        super(StatusBar, self).__init__(window)
        self._window = window  # BrowserWindow
        self._statusBarText = ''
        self._widgets = {}  # QHash<QString, WidgetData>

    def showMesssage(self, message, timeout=0):
        pass

    def clearMessage(self):
        pass

    def addButton(self, button):
        '''
        @param: button AbstractButtonInterface
        '''
        pass

    def removeButton(self, button):
        '''
        @param: button AbstractButtonInterface
        '''
        pass

    # protected
    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        pass
