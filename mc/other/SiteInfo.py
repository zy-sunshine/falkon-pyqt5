from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.Qt import Qt
from mc.common.globalvars import gVar
from PyQt5.Qt import QIcon
from PyQt5.Qt import QUrl
from mc.webengine.WebPage import WebPage
from mc.tools.Scripts import Scripts
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import QAction

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

        # TODO:
        #delegate = ListItemDelegate(24, self._ui.listWidget)
        #delegate.setUpdateParentHeight(True)
        #delegate.setUniformItemSizes(True)
        #self._ui.listWidget.setItemDelegate(delegate)

        self._ui.listWidget.item(0).setIcon(QIcon.fromTheme('document-properties',
            QIcon(':/icons/preferences/document-properties.png'),
        ))
        self._ui.listWidget.item(1).setIcon(QIcon.fromTheme('application-graphics',
            QIcon(':/icons/preferences/application-graphics.png')
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
        pass

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
            gVar.app.clipboard().setText(action.data().toString())

    def _saveImage(self):
        pass

    # private:
    def _showLoadingText(self):
        pass

    def _showPixmap(self, pixmap):
        '''
        @param: pixmap QPixmap
        '''
        pass
