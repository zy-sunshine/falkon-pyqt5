from PyQt5.Qt import QObject
from PyQt5.Qt import QPoint
from mc.app.Settings import Settings
from mc.common import const

class DesktopNotificationsFactory(QObject):
    # enum Type
    DesktopNative = 0
    PopupWidget = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False
        self._timeout = 0
        self._notifType = 0  # Type
        self._position = QPoint()

        self._desktopNotif = None  # QPointer<DesktopNotification>
        self._uint = 0  # quint32

        self.loadSettings()

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('Notifications')
        self._enabled = settings.value('Enabled', True)
        self._timeout = settings.value('Timeout', 6000)
        if const.OS_UNIX:  # && !defined(DISABLE_DBUS)
            if settings.value('UseNativeDesktop', True):
                self._notifType = self.DesktopNative
            else:
                self._notifType = self.PopupWidget
        self._position = settings.value('Position', QPoint(10, 10), type=QPoint)
        settings.endGroup()

    def supportsNativeNotifications(self):
        if const.OS_UNIX:  # && !defined(DISABLE_DBUS)
            return True
        else:
            return False

    def showNotification(self, icon, heading, text):
        '''
        @param: icon QPixmap
        @param: heading QString
        @param: text QString
        '''
        pass

    def nativeNotificationPreview(self):
        pass

    # private Q_SLOTS:
    def _updateLastId(self, msg):
        '''
        @param: msg QDBusMessage
        '''
        pass

    def _error(self, error):
        '''
        @param: error QDBusError
        '''
        pass
