from PyQt5.QtWidgets import QDialog

class NavigationBarConfigDialog(QDialog):
    def __init__(self, navigationBar):
        super().__init__(navigationBar)

    def loadSettings(self):
        pass

    def saveSettings(self):
        pass

    def resetToDefaults(self):
        pass

    def buttonClicked(self, button):
        '''
        @param: button QAbstractButton
        '''
        pass
