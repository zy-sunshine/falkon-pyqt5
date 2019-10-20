from PyQt5.Qt import QObject
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.app.Settings import Settings
from .HTML5PermissionsNotification import HTML5PermissionsNotification

class HTML5PermissionsManager(QObject):
    def __init__(self, parent):
        '''
        @param parent QObject
        '''
        super().__init__(parent)
        self._granted = {}  # QHash<QWebEnginePage::Feature, QStringList>
        self._denied = {}  # QHash<QWebEnginePage::Feature, QStringList>

        self.loadSettings()

    def requestPermissions(self, page, origin, feature):
        '''
        @param page WebPage
        @param origin QUrl
        @param feature QWebEnginePage::Feature
        '''
        if not page:
            return

        if feature not in self._granted or feature not in self._denied:
            print('WARNING: HTML5PermissionsManager: Unknown feature', feature)
            return

        # Permission granted
        if origin.toString() in self._granted[feature]:
            page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionGrantedByUser)
            return

        # Permission denied
        if origin.toString() in self._denied[feature]:
            page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionDeniedByUser)
            return

        # Ask user for permission
        notif = HTML5PermissionsNotification(origin, page, feature)
        page.view().addNotification(notif)

    def rememberPermissions(self, origin, feature, policy):
        '''
        @param origin QUrl
        @param feature QWebEnginePage::Feature
        @param policy QWebEnginePage::PermissionPolicy
        '''
        if origin.isEmpty():
            return

        if policy == QWebEnginePage.PermissionGrantedByUser:
            self._granted[feature].append(origin.toString())
        else:
            self._denied[feature].append(origin.toString())

        self._saveSettings()

    s_settingList = (
        (QWebEnginePage.Geolocation, 'Geolocation'),
        (QWebEnginePage.MediaAudioCapture, 'MediaAudioCapture'),
        (QWebEnginePage.MediaVideoCapture, 'MediaVideoCapture'),
        (QWebEnginePage.MediaAudioVideoCapture, 'MediaAudioVideoCapture'),
        (QWebEnginePage.MouseLock, 'MouseLock'),
        (QWebEnginePage.DesktopVideoCapture, 'DesktopVideoCapture'),
        (QWebEnginePage.DesktopAudioVideoCapture, 'DesktopAudioVideoCapture'),
    )

    def loadSettings(self):
        settings = Settings()
        settings.beginGroup('HTML5Notifications')
        for enumType, name in self.s_settingList:
            grantedName = '%sGranted' % name
            deniedName = '%sDenied' % name
            self._granted[enumType] = settings.value(grantedName, [])
            self._denied[enumType] = settings.value(deniedName, [])
        settings.endGroup()

    # private:
    def _saveSettings(self):
        settings = Settings()
        settings.beginGroup('HTML5Notifications')
        for enumType, name in self.s_settingList:
            grantedName = '%sGranted' % name
            deniedName = '%sDenied' % name
            settings.setValue(grantedName, self._granted[enumType])
            settings.setValue(deniedName, self._denied[enumType])
        settings.endGroup()
