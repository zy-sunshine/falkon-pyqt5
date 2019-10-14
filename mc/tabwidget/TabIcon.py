from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QRect
from PyQt5.Qt import QTimer
from PyQt5.Qt import QIcon
from PyQt5.Qt import Qt
from PyQt5.Qt import QEvent
from PyQt5.Qt import QToolTip
from PyQt5.Qt import QPainter
from PyQt5.Qt import QPalette
from mc.common import const
from mc.tools.IconProvider import IconProvider

class TabIcon(QWidget):
    class Data:
        def __init__(self):
            self.framesCount = 0
            self.animationInterval = 0
            self.animationPixmap = QPixmap()
            self.audioPlayingPixmap = QPixmap()
            self.audioMutedPixmap = QPixmap()

    def __init__(self, parent):
        '''
        @param parent QWidget
        '''
        super().__init__(parent)
        self._tab = None  # WebTab
        self._updateTimer = None  # QTimer
        self._hideTimer = None  # QTimer
        self._sitePixmap = QPixmap()
        self._currentFrame = 0
        self._animationRunning = False
        self._audioIconDisplayed = False
        self._audioIconRect = QRect()

        self.setObjectName('tab-icon')

        self._updateTimer = QTimer(self)
        self._updateTimer.setInterval(self.data().animationInterval)
        self._updateTimer.timeout.connect(self._updateAnimationFrame)

        self._hideTimer = QTimer(self)
        self._hideTimer.setInterval(250)
        self._hideTimer.timeout.connect(self._hide)

        self.resize(16, 16)

    def setWebTab(self, tab):
        '''
        @param: tab WebTab
        '''
        self._tab = tab

        self._tab.webView().loadStarted.connect(self._showLoadingAnimation)
        self._tab.webView().loadFinished.connect(self._hideLoadingAnimation)
        self._tab.webView().iconChanged.connect(self.updateIcon)
        self._tab.webView().backgroundActivityChanged.connect(lambda: self.update())

        def pageChangedCb(page):
            '''
            @param: page WebPage
            '''
            page.recentlyAudibleChanged.connect(self._updateAudioIcon)

        pageChangedCb(self._tab.webView().page())
        self._tab.webView().pageChanged.connect(pageChangedCb)

        self.updateIcon()

    def updateIcon(self):
        self._sitePixmap = self._tab.icon(True).pixmap(16)  # allowNull
        if self._sitePixmap.isNull():
            if self._tab.url().isEmpty() or self._tab.url().scheme() == const.APP_SCHEME:
                self._hide()
            else:
                self._hideTimer.start()
        else:
            self._show()
        self.update()

    _s_data = None
    def data(self):
        '''
        @return: Data
        '''
        if self._s_data is None:
            self._s_data = data = self.Data()
            data.animationInterval = 70
            data.animationPixmap = QIcon(':/icons/other/loading.png').pixmap(288, 16)
            data.framesCount = data.animationPixmap.width() / data.animationPixmap.height()
            data.audioPlayingPixmap = QIcon.fromTheme('audio-volume-high', QIcon(
                ':/icons/other/audioplaying.svg')).pixmap(16)
            data.audioMutedPixmap = QIcon.fromTheme('audio-volume-muted', QIcon(
                ':/icons/other/audiomuted.svg')).pixmap(16)
        return self._s_data

    # Q_SIGNALS
    resized = pyqtSignal()

    # private Q_SLOTS:
    def _showLoadingAnimation(self):
        self._currentFrame = 0
        self._updateAnimationFrame()
        self._show()

    def _hideLoadingAnimation(self):
        self._animationRunning = False
        self._updateTimer.stop()
        self.updateIcon()

    def _updateAudioIcon(self, recentlyAudible):
        if self._tab.isMuted() or recentlyAudible:
            self._audioIconDisplayed = True
            self._show()
        else:
            self._audioIconDisplayed = False
            self._hide()

        self.update()

    def _updateAnimationFrame(self):
        if not self._animationRunning:
            self._updateTimer.start()
            self._animationRunning = True

        self.update()
        self._currentFrame = (self._currentFrame + 1) % self.data().framesCount

    # private:
    def _show(self):
        if not self._shouldBeVisible():
            return

        self._hideTimer.stop()

        if self.isVisible() and self.width() == 16:
            return

        self.setFixedSize(16, max(self.minimumHeight(), 16))
        self.resized.emit()
        super().show()

    def _hide(self):
        if self._shouldBeVisible():
            return

        if self.isHidden() and self.width() == 1:
            return

        self.setFixedSize(1, max(self.minimumHeight(), 16))
        self.resized.emit()
        super().hide()

    def _shouldBeVisible(self):
        return not self._sitePixmap.isNull() or self._animationRunning or \
            self._audioIconDisplayed or (self._tab and self._tab.isPinned())

    # override
    def event(self, event):
        '''
        @param: event QEvent
        '''
        if event.type() == QEvent.ToolTip:
            # QHelpEvent
            if self._audioIconDisplayed and self._audioIconRect.contains(event.pos()):
                QToolTip.showText(event.globalPos(), self._tab.isMuted() and _('Unmute Tab') or _('Mute Tab'), self)
                event.accept()
                return True
        return super().event(event)

    # override
    def paintEvent(self, event):
        '''
        @param event QPaintEvent
        '''
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        size = 16
        pixmapSize = round(size * self.data().animationPixmap.devicePixelRatioF())

        # Center the pixmap in rect
        r = QRect(self.rect())
        r.setX((r.width() - size) / 2)
        r.setY((r.height() - size) / 2)
        r.setWidth(size)
        r.setHeight(size)

        if self._animationRunning:
            p.drawPixmap(r, self.data().animationPixmap,
                QRect(self._currentFrame * pixmapSize, 0, pixmapSize, pixmapSize))
        elif self._audioIconDisplayed and not self._tab.isPinned():
            self._audioIconRect = QRect(r)
            p.drawPixmap(r, self._tab.isMuted() and self.data().audioMutedPixmap or
                    self.data().audioPlayingPixmap)
        elif not self._sitePixmap.isNull():
            p.drawPixmap(r, self._sitePixmap)
        elif self._tab and self._tab.isPinned():
            p.drawPixmap(r, IconProvider.emptyWebIcon().pixmap(size))

        # Draw audio icon on top of site icon for pinned tabs
        if not self._animationRunning and self._audioIconDisplayed and self._tab.isPinned():
            s = size - 4
            r0 = QRect(self.width() - 4, 0, s, s)
            self._audioIconRect = r0
            c = self.palette().color(QPalette.Window)
            c.setAlpha(180)
            p.setPen(c)
            p.setBrush(c)
            p.drawEllipse(r)
            p.drawPixmap(r, self._tab.isMuted() and self.data().audioMutedPixmap or
                    self.data().audioPlayingPixmap)

        # Draw background activity indicator
        if self._tab and self._tab.isPinned() and self._tab.webView().backgroundActivity():
            s = 5
            # Background
            r1 = QRect(self.width() - s - 2, self.height() - s - 2, s + 2, s + 2)
            c1 = self.palette().color(QPalette.Window)
            c1.setAlpha(180)
            p.setPen(Qt.transparent)
            p.setBrush(c1)
            p.drawEllipse(r1)
            # Forground
            r2 = QRect(self.width() - s - 1, self.height() - s - 1, s, s)
            c2 = self.palette().color(QPalette.Text)
            p.setPen(Qt.transparent)
            p.setBrush(c2)
            p.drawEllipse(r2)

    # override
    def mousePressEvent(self, event):
        '''
        @param event QMouseEvent
        '''
        if self._audioIconDisplayed and event.button() == Qt.LeftButton and \
                self._audioIconRect.contains(event.pos()):
            self._tab.toggleMuted()
            return

        super().mousePressEvent(event)
