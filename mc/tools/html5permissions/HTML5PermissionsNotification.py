from PyQt5 import uic
from PyQt5.Qt import QStyle
from PyQt5.Qt import QTimer
from PyQt5.Qt import QCursor
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from mc.tools.IconProvider import IconProvider
from mc.common.globalvars import gVar
from mc.tools.AnimatedWidget import AnimatedWidget

class HTML5PermissionsNotification(AnimatedWidget):
    def __init__(self, origin, page, feature):
        '''
        @param origin QUrl
        @param page QWebEnginePage
        @param feature QWenEnginePage.Feature
        '''
        super().__init__(AnimatedWidget.Down, 300, None)
        self._ui = uic.loadUi('mc/tools/html5permissions/HTML5PermissionsNotification.ui', self.widget())
        self._origin = origin
        self._page = page  # QPointer<QWebEnginePage>
        self._feature = feature

        self._ui.close.setIcon(IconProvider.standardIcon(QStyle.SP_DialogCloseButton))

        if not self._origin.host():
            site = _('this site')
        else:
            site = '<b>%s</b>' % self._origin.host()

        #if feature == QWebEnginePage::Notifications:
        #   ui.textLabel.setText(_("Allow %s to show desktop notifications?") % site)

        if feature == QWebEnginePage.Geolocation:
            self._ui.textLabel.setText(_("Allow %s to locate your position?") % site)
        elif feature == QWebEnginePage.MediaAudioCapture:
            self._ui.textLabel.setText(_("Allow %s to use your microphone?") % site)
        elif feature == QWebEnginePage.MediaVideoCapture:
            self._ui.textLabel.setText(_("Allow %s to use your camera?") % site)
        elif feature == QWebEnginePage.MediaAudioVideoCapture:
            self._ui.textLabel.setText(_("Allow %s to use your microphone and camera?") % site)
        elif feature == QWebEnginePage.MouseLock:
            self._ui.textLabel.setText(_("Allow %s to hide your pointer?") % site)
        else:
            print('WARNING: Unknown feature', feature)

        self._ui.allow.clicked.connect(self._grantPermissions)
        self._ui.deny.clicked.connect(self._denyPermissions)
        self._ui.close.clicked.connect(self._denyPermissions)

        self._page.loadStarted.connect(self.deleteLater)

        def cb(origin, feature):
            '''
            @param: origin QUrl
            @param: feature QWebEnginePage::Feature
            '''
            if origin == self._origin and feature == self._feature:
                self.deleteLater()
        self._page.featurePermissionRequestCanceled.connect(cb)

        self.startAnimation()

    # private Q_SLOTS:
    def _grantPermissions(self):
        if not self._page:
            return

        QTimer.singleShot(0, self._grantPermissionsCb)

    def _grantPermissionsCb(self):
        # We need to have cursor inside view to correctly grab mouse
        if self._feature == QWebEnginePage.MouseLock:
            # QWidget
            view = self._page.view()
            QCursor.setPos(view.mapToGlobal(view.rect().center()))
        self._page.setFeaturePermission(self._origin, self._feature,
                QWebEnginePage.PermissionGrantedByUser)

        if self._ui.remember.isChecked():
            gVar.app.html5PermissionsManager().rememberPermissions(self._origin,
                    self._feature, QWebEnginePage.PermissionGrantedByUser)

        self.hide()

    def _denyPermissions(self):
        if not self._page:
            return

        self._page.setFeaturePermission(self._origin, self._feature,
                QWebEnginePage.PermissionDeniedByUser)

        if self._ui.remember.isChecked():
            gVar.app.html5PermissionsManager().rememberPermissions(self._origin,
                    self._feature, QWebEnginePage.PermissionDeniedByUser)

        self.hide()
