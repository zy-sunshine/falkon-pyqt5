from os.path import join as pathjoin
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.Qt import QIcon
from PyQt5.Qt import QUrl
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import QAction
from PyQt5.Qt import QDir
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import QGraphicsScene
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QImage
from PyQt5.Qt import QNetworkReply
from PyQt5.Qt import QNetworkRequest

from mc.common.globalvars import gVar
from mc.webengine.WebPage import WebPage
from mc.tools.Scripts import Scripts
from mc.tools.ListItemDelegate import ListItemDelegate

class SiteInfo(QDialog):
    def __init__(self, view):
        '''
        @param: view WebView
        '''
        super().__init__(view)
        self._ui = None  # Ui::SiteInfo
        self._certWidget = None  # CertificateInfoWidget
        self._view = view  # WebView
        self._imageReply = None  # QNetworkReply
        self._baseUrl = QUrl()

        self._ui = uic.loadUi('mc/other/SiteInfo.ui', self)
        self._ui.treeTags.setLayoutDirection(Qt.LeftToRight)
        gVar.appTools.centerWidgetOnScreen(self)

        delegate = ListItemDelegate(24, self._ui.listWidget)
        delegate.setUpdateParentHeight(True)
        delegate.setUniformItemSizes(True)
        self._ui.listWidget.setItemDelegate(delegate)

        self._ui.listWidget.item(0).setIcon(QIcon.fromTheme('document-properties',
            QIcon(':/icons/preferences/document-properties.png'),
        ))
        self._ui.listWidget.item(1).setIcon(QIcon.fromTheme('applications-graphics',
            QIcon(':/icons/preferences/applications-graphics.png')
        ))
        self._ui.listWidget.item(0).setSelected(True)

        # General
        self._ui.heading.setText('<b>%s</b>:' % self._view.title())
        self._ui.siteAddress.setText(self._view.url().toString())

        if self._view.url().scheme() == 'https':
            self._ui.securityLabel.setText('<b>Connection is Encrypted.</b>')
        else:
            self._ui.securityLabel.setText('<b>Connection Not Encrypted.</b>')

        self._view.page().runJavaScript('document.charset', WebPage.SafeJsWorld,
                lambda res: self._ui.encodingLabel.setText(res))

        # Meta
        def metaFunc(res):
            for meta in res:
                content = meta['content']
                name = meta['name']

                if not name:
                    name = meta['httpequiv']

                if not content or not name:
                    continue

                item = QTreeWidgetItem(self._ui.treeTags)
                item.setText(0, name)
                item.setText(1, content)
                self._ui.treeTags.addTopLevelItem(item)

        self._view.page().runJavaScript(Scripts.getAllMetaAttributes(),
            WebPage.SafeJsWorld, metaFunc)

        # Images
        def imageFunc(res):
            for val in res:
                img = val
                src = img['src']
                alt = img['alt']
                if not alt:
                    if src.find('/') == 1:
                        alt = src
                    else:
                        pos = src.rfind('/')
                        alt = src[pos+1:]

                if not src or not alt:
                    continue

                item = QTreeWidgetItem(self._ui.treeImages)
                item.setText(0, alt)
                item.setText(1, src)
                self._ui.treeImages.addTopLevelItem(item)

        self._view.page().runJavaScript(Scripts.getAllImages(), WebPage.SafeJsWorld,
                imageFunc)

        self._ui.saveButton.clicked.connect(self._saveImage)
        self._ui.listWidget.currentRowChanged.connect(self._ui.stackedWidget.setCurrentIndex)
        self._ui.treeImages.currentItemChanged.connect(self._showImagePreview)
        self._ui.treeImages.customContextMenuRequested.connect(self._imagesCustomContextMenuRequested)

        self._ui.treeImages.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.treeImages.sortByColumn(-1, Qt.AscendingOrder)

        self._ui.treeTags.sortByColumn(-1, Qt.AscendingOrder)

        gVar.appTools.setWmClass('Site Info', self)

    @classmethod
    def canShowSiteInfo(cls, url):
        '''
        @param: url QUrl
        @return: bool
        '''
        from mc.navigation.LocationBar import LocationBar
        if not LocationBar.convertUrlToText(url):
            return False

        scheme = url.scheme()
        if scheme == 'app' or scheme == 'view-source' or scheme == 'extension':
            return False

        return True

    # private Q_SLOTS:
    def _showImagePreview(self, item):
        '''
        @param: item QTreeWidgetItem
        '''
        if not item:
            return

        imageUrl = QUrl.fromEncoded(item.text(1).encode())
        if imageUrl.isRelative():
            imageUrl = self._baseUrl.resolved(imageUrl)

        pixmap = QPixmap()
        loading = False

        if imageUrl.scheme() == 'data':
            # QByteArray
            encodedUrl = item.text(1)
            # QByteArray
            imageData = encodedUrl[encodedUrl.find(',') + 1:]
            pixmap = gVar.appTools.pixmapFromByteArray(imageData)
        elif imageUrl.scheme() == 'file':
            pixmap = QPixmap(imageUrl.toLocalFile())
        elif imageUrl.scheme() == 'qrc':
            pixmap = QPixmap(imageUrl.toString()[:3])  # Remove qrc from url
        else:
            self._imageReply = gVar.app.networkManager().get(QNetworkRequest(imageUrl))

            def imageReplyCb():
                if self._imageReply.error() != QNetworkReply.NoError:
                    return

                # QByteArray
                data = self._imageReply.readAll()
                self._showPixmap(QPixmap.fromImage(QImage.fromData(data)))
            self._imageReply.finished.connect(imageReplyCb)
            loading = True
            self._showLoadingText()

        if not loading:
            self._showPixmap(pixmap)

    def _imagesCustomContextMenuRequested(self, point):
        '''
        @param: point QPoint
        '''
        item = self._ui.treeImages.itemAt(point)
        if not item:
            return

        menu = QMenu()
        action = menu.addAction(QIcon.fromTheme('edit-copy'), _('Copy Image Location'),
                self._copyActionData)
        action.setData(item.text(1))
        menu.addSeparator()
        menu.addAction(QIcon.fromTheme('document-save'), _('Save Image to Disk'),
                self._saveImage)

        menu.exec_(self._ui.treeImages.viewport().mapToGlobal(point))

    def _copyActionData(self):
        action = self.sender()
        if isinstance(action, QAction):
            gVar.app.clipboard().setText(action.data())

    def _saveImage(self):
        item = self._ui.treeImages.currentItem()
        if not item:
            return

        if not self._ui.mediaPreview.scene() or not self._ui.mediaPreview.scene().items():
            return

        # QGraphicsItem
        graphicsItem = self._ui.mediaPreview.scene().items()[0]
        if graphicsItem.type() != QGraphicsPixmapItem.Type or \
                not isinstance(graphicsItem, QGraphicsPixmapItem):
            return

        pixmapItem = graphicsItem
        if pixmapItem.pixmap().isNull():
            QMessageBox.warning(self, _('Error!'), _('This preview is not available!'))
            return

        imageFileName = gVar.appTools.getFileNameFromUrl(QUrl(item.text(1)))
        index = imageFileName.rfind('.')
        if index != -1:
            imageFileName = imageFileName[:index]
            imageFileName += '.png'

        filePath = gVar.appTools.getSaveFileName('SiteInfo-DownloadImage', self, _('Save image...'),
                pathjoin(QDir.homePath(), imageFileName), '*.png')

        if not filePath:
            return

        if not pixmapItem.pixmap().save(filePath, 'PNG'):
            QMessageBox.critical(self, _('Error!'), _('Cannot write to file!'))
            return

    # private:
    def _showLoadingText(self):
        scene = QGraphicsScene(self._ui.mediaPreview)

        scene.addText(_('Loading...'))

        self._ui.mediaPreview.setScene(scene)

    def _showPixmap(self, pixmap):
        '''
        @param: pixmap QPixmap
        '''
        pixmap.setDevicePixelRatio(self.devicePixelRatioF())

        scene = QGraphicsScene(self._ui.mediaPreview)

        if pixmap.isNull():
            scene.addText(_('Preview not available'))
        else:
            scene.addPixmap(pixmap)

        self._ui.mediaPreview.setScene(scene)
