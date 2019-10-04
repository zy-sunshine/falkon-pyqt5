from mc.tools.AbstractButtonInterface import AbstractButtonInterface
from PyQt5.Qt import QIcon
from mc.common.globalvars import gVar

class DownloadsButton(AbstractButtonInterface):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = gVar.app.downloadManager()  # DownloadManager
        self.setIcon(QIcon.fromTheme('edit-download', QIcon(':/icons/menu/download.svg')))
        self.setTitle('Downloads')
        self.setToolTip('Open Download Manager')

        self.clicked.connect(self._clicked)
        self._manager.downloadsCountChanged.connect(self._updateState)
        self._updateState()

    # override
    def id(self):
        return 'button-downloads'

    # override
    def name(self):
        return 'Downloads'

    # private:
    def _updateState(self):
        # self.setVisible(self._manager.downloadsCount() > 0)
        self.setVisible(True)
        count = self._manager.activeDownloadsCount()
        if count > 0:
            self.setBadgeText(str(count))
        else:
            self.setBadgeText('')

    def _clicked(self, controller):
        '''
        @param: ClickController
        '''
        import ipdb; ipdb.set_trace()
        gVar.app.downloadManager().show()
