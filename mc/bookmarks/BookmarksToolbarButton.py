from PyQt5.QtWidgets import QPushButton
from PyQt5.Qt import QPoint
from PyQt5.Qt import Qt
from PyQt5.Qt import QSizePolicy
from PyQt5.Qt import QApplication
from PyQt5.Qt import QUrl
from PyQt5.Qt import QAction
from PyQt5.Qt import QDrag
from PyQt5.Qt import QPainter
from PyQt5.Qt import QStyleOption
from PyQt5.Qt import QStyle
from PyQt5.Qt import QStyleOptionButton
from PyQt5.Qt import QCursor
from PyQt5.Qt import QRect
from mc.tools.EnhancedMenu import Menu
from mc.common.globalvars import gVar
from .BookmarksTools import BookmarksTools
from .BookmarkItem import BookmarkItem
from .BookmarksModel import BookmarksButtonMimeData

class BookmarksToolbarButton(QPushButton):
    MAX_WIDTH = 150
    SEPARATOR_WIDTH = 8
    PADDING = 5
    def __init__(self, bookmark, parent=None):
        super().__init__(parent)
        self._bookmark = bookmark  # BookmarkItem
        self._window = None  # BrowserWindow

        self._showOnlyIcon = False
        self._showOnlyText = True
        self._dragStartPosition = QPoint()

        self._init()

        if self._bookmark.isFolder():
            self.acceptDrops(True)

    def bookmark(self):
        '''
        @return: BookmarkItem
        '''
        return self._bookmark

    def setMainWindow(self, window):
        '''
        @param: window BrowserWindow
        '''
        self._window = window

    def showOnlyIcon(self):
        return self._showOnlyIcon

    def setShowOnlyIcon(self, show):
        self._showOnlyIcon = show
        self.updateGeometry()
        self.update()

    def showOnlyText(self):
        self._showOnlyText

    def setShowOnlyText(self, show):
        self._showOnlyText = show
        self.updateGeometry()
        self.update()

    # override
    def sizeHint(self):
        width = self.PADDING * 2
        if not self._showOnlyText:
            width += 16

        if self._bookmark.isSeparator():
            width = self.SEPARATOR_WIDTH
        elif not self._showOnlyIcon:
            width += self.PADDING * 2 + self.fontMetrics().width(self._bookmark.title())

            if self.menu():
                width += self.PADDING + 8

        sz = super().sizeHint()
        sz.setWidth(min(width, self.MAX_WIDTH))
        return sz

    # override
    def minimumSizeHint(self):
        width = self.PADDING * 2
        if not self._showOnlyText:
            width += 16

        if self._bookmark.isSeparator():
            width = self.SEPARATOR_WIDTH
        elif not self._showOnlyIcon and self.menu():
            width += self.PADDING + 8

        sz = super().minimumSizeHint()
        sz.setWidth(width)
        return sz

    # private Q_SLOTS:
    def _createMenu(self):
        if not self.menu().isEmpty():
            return

        m = self.menu()
        assert(isinstance(m, Menu))

        BookmarksTools.addFolderContentsToMenu(self, m, self._bookmark)

    def _menuAboutToShow(self):
        menu = self.sender()
        assert(isinstance(menu, Menu))

        for action in menu.actions():
            item = action.data()
            if isinstance(item, BookmarkItem) and item.type() == BookmarkItem.Url and \
                    action.icon().isNull():
                action.setIcon(item.icon())

    def _menuMiddleClicked(self, menu):
        item = menu.menuAction().data()
        assert(isinstance(item, BookmarkItem))
        self._openFolder(item)

    def _bookmarkActivated(self, item=None):
        action = self.sender()
        if isinstance(action, QAction):
            item = action.data()
        assert(isinstance(item, BookmarkItem))
        self._openBookmark(item)

    def _bookmarkCtrlActivated(self, item=None):
        action = self.sender()
        if isinstance(action, QAction):
            item = action.data()
        assert(isinstance(item, BookmarkItem))
        self._openBookmarkInNewTab(item)

    def _bookmarkShiftActivated(self, item=None):
        action = self.sender()
        if isinstance(action, QAction):
            item = action.data()
        assert(isinstance(item, BookmarkItem))
        self._openBookmarkInNewWindow(item)

    def _openFolder(self, item):
        assert(item.isFolder())

        if self._window:
            BookmarksTools.openFolderInTabs(self._window, item)

    def _openBookmark(self, item):
        assert(item.isUrl())

        if self._window:
            BookmarksTools.openBookmark(self._window, item)

    def _openBookmarkInNewTab(self, item):
        assert(item.isUrl())

        if self._window:
            BookmarksTools.openBookmarkInNewTab(self._window, item)

    def _openBookmarkInNewWindow(self, item):
        assert(item.isUrl())

        if self._window:
            BookmarksTools.openBookmarkInNewWindow(self._window, item)

    # private:
    def _init(self):
        assert(self._bookmark)

        self.setFocusPolicy(Qt.NoFocus)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setToolTip(self._createTooltip())

        if self._bookmark.isFolder():
            menu = Menu(self)
            self.setMenu(menu)
            self._createMenu()

    def _createTooltip(self):
        '''
        @return: QString
        '''
        desc = self._bookmark.description()
        urlStr = self._bookmark.urlString()
        title = self._bookmark.title()
        url = self._bookmark.url()
        if desc:
            if urlStr:
                return '%s\n%s' % (desc, urlStr)
            return desc

        if title and url:
            return '%s\n%s' % (title, urlStr)

        if title:
            return title

        return urlStr

    # override
    def enterEvent(self, event):
        '''
        @param: event QEvent
        '''
        super().enterEvent(event)
        self.update()

    # override
    def leaveEvent(self, event):
        '''
        @param: event QEvent
        '''
        super().leaveEvent(event)
        self.update()

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if self._bookmark and self._bookmark.isFolder():
            if event.buttons() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
                self._openFolder(self._bookmark)
                return

        self._dragStartPosition = event.pos()

        super().mousePressEvent(event)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if self._bookmark and self.rect().contains(event.pos()):
            # Qt::MouseButton
            button = event.button()
            # Qt::KeyboardModifiers
            modifiers = event.modifiers()

            if self._bookmark.isUrl():
                if button == Qt.LeftButton and modifiers == Qt.NoModifier:
                    self._bookmarkActivated(self._bookmark)
                elif button == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                    self._bookmarkShiftActivated(self._bookmark)
                elif button == Qt.MiddleButton or modifiers == Qt.ControlModifier:
                    self._bookmarkCtrlActivated(self._bookmark)
            elif self._bookmark.isFolder() and button == Qt.MiddleButton:
                self._openFolder(self._bookmark)

        super().mouseReleaseEvent(event)

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if (event.pos() - self._dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        self.setDown(False)

        drag = QDrag(self)
        mime = BookmarksButtonMimeData()
        mime.setBookmarkItem(self._bookmark)
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.exec_()

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        p = QPainter(self)

        # Just draw separator
        if self._bookmark.isSeparator():
            opt = QStyleOption()
            opt.initFrom(self)
            opt.state |= QStyle.State_Horizontal
            self.style().drawPrimitive(QStyle.PE_IndicatorToolBarSeparator, opt, p)
            return

        option = QStyleOptionButton()
        self.initStyleOption(option)

        # We are manually drawing the arrow
        option.features &= ~QStyleOptionButton.HasMenu

        # Draw button base (only under mouse, this is autoraise button)
        if self.isDown() or self.hitButton(self.mapFromGlobal(QCursor.pos())):
            option.state |= QStyle.State_AutoRaise | QStyle.State_Raised
            self.style().drawPrimitive(QStyle.PE_PanelButtonTool, option, p, self)

        if self.isDown():
            shiftX = self.style().pixelMetric(QStyle.PM_ButtonShiftHorizontal, option, self)
            shiftY = self.style().pixelMetric(QStyle.PM_ButtonShiftVertical, option, self)
        else:
            shiftX = 0
            shiftY = 0

        height = option.rect.height()
        center = height / 2 + option.rect.top() + shiftY

        iconSize = 16
        iconYPos = center - iconSize / 2

        leftPosition = self.PADDING + shiftX
        rightPosition = option.rect.right() - self.PADDING

        # Draw icon
        if not self._showOnlyText:
            iconRect = QRect(leftPosition, iconYPos, iconSize, iconSize)
            p.drawPixmap(QStyle.visualRect(option.direction, option.rect, iconRect),
                    self._bookmark.icon().pixmap(iconSize))
            leftPosition = iconRect.right() + self.PADDING

        # Draw menu arrow
        if not self._showOnlyIcon and self.menu():
            arrowSize = 8
            opt = QStyleOption()
            opt.initFrom(self)
            rect = QRect(rightPosition - 8, center - arrowSize / 2, arrowSize, arrowSize)
            opt.rect = QStyle.visualRect(option.direction, option.rect, rect)
            opt.state &= ~QStyle.State_MouseOver
            self.style().drawPrimitive(QStyle.PE_IndicatorArrowDown, opt, p, self)
            rightPosition = rect.left() - self.PADDING

        # Draw text
        if not self._showOnlyIcon:
            textWidth = rightPosition - leftPosition
            textYPos = center - self.fontMetrics().height() / 2
            txt = self.fontMetrics().elidedText(self._bookmark.title(), Qt.ElideRight, textWidth)
            textRect = QRect(leftPosition, textYPos, textWidth, self.fontMetrics().height())
            self.style().drawItemText(p, QStyle.visualRect(option.direction, option.rect, textRect),
                    Qt.TextSingleLine | Qt.AlignCenter, option.palette, True, txt)

    # override
    def dragEnterEvent(self, event):
        '''
        @param: event QDragEnterEvent
        '''
        mime = event.mimeData()
        if (mime.hasUrls() and mime.hasText()) or mime.hasFormat(BookmarksButtonMimeData.mimeType()):
            event.acceptProposedAction()
            self.setDown(True)
            return
        super().dragEnterEvent(event)

    # override
    def dragLeaveEvent(self, event):
        '''
        @param: event QDragLeaveEvent
        '''
        self.setDown(False)

    # override
    def dropEvent(self, event):
        '''
        @param: event QDropEvent
        '''
        self.setDown(False)

        mime = event.mimeData()
        if not mime.hasUrls() and not mime.hasFormat(BookmarksButtonMimeData.mimeType()):
            super().dropEvent(event)
            return

        bookmark = None

        if mime.hasFormat(BookmarksButtonMimeData.mimeType()):
            bookmarkMime = mime
            assert(isinstance(bookmarkMime, BookmarksButtonMimeData))
            bookmark = bookmarkMime.item()
        else:
            url = mime.urls()[0]
            if mime.hasText():
                title = mime.text()
            else:
                title = url.toEncoded(QUrl.RemoveScheme)

            bookmark = BookmarkItem(BookmarkItem.Url)
            bookmark.setTitle(title)
            bookmark.setUrl(url)

        gVar.app.bookmarks().addBookmark(self._bookmark, bookmark)
