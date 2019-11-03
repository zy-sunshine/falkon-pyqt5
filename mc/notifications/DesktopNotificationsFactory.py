from PyQt5.Qt import QObject
from PyQt5.Qt import QPoint
from PyQt5.Qt import QFile
from mc.app.Settings import Settings
from mc.common import const
from mc.app.DataPaths import DataPaths
from mc.common.globalvars import gVar
from .DesktopNotification import DesktopNotification

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
        if not self._enabled:
            return

        if self._notifType == self.PopupWidget:
            if not self._desktopNotif:
                self._desktopNotif = DesktopNotification()

                def func():
                    self._desktopNotif = None
                self._desktopNotif.closedSignal.connect(func)
            self._desktopNotif.setPixmap(icon)
            self._desktopNotif.setHeading(heading)
            self._desktopNotif.setText(text)
            self._desktopNotif.setTimeout(self._timeout)
            self._desktopNotif.move(self._position)
            self._desktopNotif.show()
        elif self._notifType == self.DesktopNative:
            if const.OS_UNIX and not const.DISABLE_DBUS:
                tmp = QFile(DataPaths.path(DataPaths.Temp) + '/app_notif.png')
                tmp.open(QFile.WriteOnly)
                icon.save(tmp.fileName())

                from PyQt5.Qt import QDBusInterface, QDBusConnection
                dbus = QDBusInterface('org.freedesktop.Notifications', '/org/freedesktop/Notifications',
                        'org.freedesktop.Notifications', QDBusConnection.sessionBus())
                args = []
                args.append('app')
                args.append(self._uint)
                args.append(tmp.fileName())
                args.append(heading)
                args.append(text)
                args.append([])
                args.append({})
                args.append(self._timeout)
                dbus.callWithCallback('Notify', args, self._updateLastId, self._error)

    def nativeNotificationPreview(self):
        type_ = self._notifType
        self._notifType = self.DesktopNative
        icon = gVar.app.getWindow().windowIcon().pixmap(64)
        self.showNotification(icon, _('Native System Notification'), _('Preview'))
        self._notifType = type_

    # private Q_SLOTS:
    def _updateLastId(self, msg):
        '''
        @param: msg QDBusMessage
        '''
        if const.OS_UNIX and not const.DISABLE_DBUS:
            list_ = msg.arguments()
            if len(list_) > 0:
                self._uint = list_[0]
                assert(type(self._uint) == int)

    def _error(self, error):
        '''
        @param: error QDBusError
        '''
        if const.OS_UNIX and not const.DISABLE_DBUS:
            print('Warning: QDBusError:', error.message())
