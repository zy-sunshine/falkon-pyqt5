from mc.tools.ClickableLabel import ClickableLabel
from PyQt5.Qt import Qt

class AutoFillIcon(ClickableLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._view = None  # WebView
        self._usernames = []  # QStringList

        self.setObjectName('locationbar-autofillicon')
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(_('Choose username to login'))
        self.setFocusPolicy(Qt.ClickFocus)

        self.clicked.connect(self._iconClicked)

    def setWebView(self, view):
        '''
        @param: view WebView
        '''
        self._view = view

    def setUsernames(self, usernames):
        '''
        @param: usernames QStringList
        '''
        self._usernames = usernames

    # private Q_SLOTS:
    def _iconClicked(self):
        if not self._view:
            return

        widget = AutoFillWidget(self._view, self)
        widget.setUsernames(self._usernames)
        widget.showAt(self.parentWidget())

    # private:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        # Prevent propagating to LocationBar
        event.accept()

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        super().mousePressEvent(event)

        # Prevent propagating to LocationBar
        event.accept()
