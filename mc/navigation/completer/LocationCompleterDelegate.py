from urllib.parse import unquote
from PyQt5.Qt import QStyledItemDelegate
from PyQt5.Qt import QStyleOptionViewItem
from PyQt5.Qt import QApplication
from PyQt5.Qt import QStyle
from PyQt5.Qt import QFontMetrics
from PyQt5.Qt import QTextOption
from PyQt5.Qt import QTextLayout
from PyQt5.Qt import QFont
from PyQt5.Qt import QTextCharFormat
from PyQt5.Qt import QIcon
from PyQt5.Qt import QPalette
from PyQt5.Qt import Qt
from PyQt5.Qt import QRect
from PyQt5.Qt import QSize
from PyQt5.Qt import QPoint
from PyQt5.Qt import QSizeF
from PyQt5.Qt import QPointF
from mc.common import const
from mc.common.globalvars import gVar
from mc.tools.IconProvider import IconProvider
from .LocationCompleterModel import LocationCompleterModel

class LocationCompleterDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        '''
        @param parent QObject
        '''
        super().__init__(parent)
        self._rowHeight = 0
        self._padding = 0
        self._forceVisitItem = False

    # override
    def paint(self, painter, option, index):  # noqa C901
        '''
        @param painter QPainter
        @param option index QStyleOptionViewItem
        @param option index QModelIndex
        '''
        from ..LocationBar import LocationBar
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        w = opt.widget
        if w:
            style = w.style()
        else:
            style = QApplication.style()

        height = opt.rect.height()
        center = height / 2 + opt.rect.top()

        # Prepare link font
        # QFont
        linkFont = opt.font
        linkFont.setPointSize(linkFont.pointSize() - 1)

        linkMetrics = QFontMetrics(linkFont)

        leftPosition = self._padding * 2
        rightPosition = opt.rect.right() - self._padding

        opt.state |= QStyle.State_Active

        if opt.state & QStyle.State_Selected:
            iconMode = QIcon.Selected
            colorRole = QPalette.HighlightedText
            colorLinkRole = QPalette.HighlightedText
        else:
            iconMode = QIcon.Normal
            colorRole = QPalette.Text
            colorLinkRole = QPalette.Link

        if const.OS_WIN:
            opt.palette.setColor(QPalette.All, QPalette.HighlightedText,
                opt.palette.color(QPalette.Active, QPalette.Text))
            opt.palette.setColor(QPalette.All, QPalette.Highlight,
                opt.palette.base().color().darker(108))

        textPalette = QPalette(opt.palette)
        if opt.state & QStyle.State_Enabled:
            textPalette.setCurrentColorGroup(QPalette.Normal)
        else:
            textPalette.setCurrentColorGroup(QPalette.Disabled)

        # Draw background
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, opt, painter, w)

        isVisitSearchItem = index.data(LocationCompleterModel.VisitSearchItemRole)
        isSearchSuggestion = index.data(LocationCompleterModel.SearchSuggestionRole)

        loadAction = LocationBar.LoadAction()
        isWebSearch = isSearchSuggestion

        # BookmarkItem
        bookmark = index.data(LocationCompleterModel.BookmarkItemRole)

        if isVisitSearchItem:
            text = index.data(LocationCompleterModel.SearchStringRole)
            loadAction = LocationBar.loadAction(text)
            isWebSearch = loadAction.type == LocationBar.LoadAction.Search
            if not self._forceVisitItem:
                bookmark = loadAction.bookmark

        # Draw icon
        iconSize = 16
        iconYPos = center - iconSize / 2
        iconRect = QRect(leftPosition, iconYPos, iconSize, iconSize)
        icon = index.data(Qt.DecorationRole)
        if not icon:
            icon = QIcon()
        pixmap = icon.pixmap(iconSize)
        if isSearchSuggestion or (isVisitSearchItem and isWebSearch):
            pixmap = QIcon.fromTheme('edit-find', QIcon(':/icons/menu/search-icon.svg')).pixmap(iconSize, iconMode)
        if isVisitSearchItem and bookmark:
            pixmap = bookmark.icon().pixmap(iconSize)
        elif loadAction.type == LocationBar.LoadAction.Search:
            if loadAction.searchEngine.name != LocationBar.searchEngine().name:
                pixmap = loadAction.searchEngine.icon.pixmap(iconSize)

        painter.drawPixmap(iconRect, pixmap)
        leftPosition = iconRect.right() + self._padding * 2

        # Draw star to bookmark items
        starPixmapWidth = 0
        if bookmark:
            icon = IconProvider.instance().bookmarkIcon
            starSize = QSize(16, 16)
            starPixmapWidth = starSize.width()
            pos = QPoint(rightPosition - starPixmapWidth, center - starSize.height() / 2)
            starRect = QRect(pos, starSize)
            painter.drawPixmap(starRect, icon.pixmap(starSize, iconMode))

        searchText = index.data(LocationCompleterModel.SearchStringRole)

        # Draw title
        leftPosition += 2
        titleRect = QRect(leftPosition, center - opt.fontMetrics.height() / 2,
                opt.rect.width() * 0.6, opt.fontMetrics.height())
        title = index.data(LocationCompleterModel.TitleRole)
        painter.setFont(opt.font)

        if isVisitSearchItem:
            if bookmark:
                title = bookmark.title()
            else:
                title = index.data(LocationCompleterModel.SearchStringRole)
                searchText = ''

        leftPosition += self.viewItemDrawText(painter, opt, titleRect, title,
                textPalette.color(colorRole), searchText)
        leftPosition += self._padding * 2

        # Trim link to maximum number characters that can be visible,
        # otherwise there may be perf issue with huge URLs
        maxChars = int((opt.rect.width() - leftPosition) / opt.fontMetrics.width('i'))
        link = index.data(Qt.DisplayRole)
        if not link.startswith('data') and not link.startswith('javascript'):
            link = unquote(link)[:maxChars]
        else:
            link = link[:maxChars]

        if isVisitSearchItem or isSearchSuggestion:
            if not (opt.state & QStyle.State_Selected) and not (opt.state & QStyle.State_MouseOver):
                link = ''
            elif isVisitSearchItem and (not isWebSearch or self._forceVisitItem):
                link = _('Visit')
            else:
                searchEngineName = loadAction.searchEngine.name
                if not searchEngineName:
                    searchEngineName = LocationBar.searchEngine().name
                link = _('Search with %s') % searchEngineName

        if bookmark:
            link = bookmark.url().toString()

        # Draw separator
        if link:
            separator = '-'
            separatorRect = QRect(leftPosition, center - linkMetrics.height() / 2,
                    linkMetrics.width(separator), linkMetrics.height())
            style.drawItemText(painter, separatorRect, Qt.AlignCenter, textPalette,
                    True, separator, colorRole)
            leftPosition += separatorRect.width() + self._padding * 2

        # Draw link
        leftLinkEdge = leftPosition
        rightLinkEdge = rightPosition - self._padding - starPixmapWidth
        linkRect = QRect(leftLinkEdge, center - linkMetrics.height() / 2,
                rightLinkEdge - leftLinkEdge, linkMetrics.height())
        painter.setFont(linkFont)

        # Darw url (or switch to tab)
        tabPos = index.data(LocationCompleterModel.TabPositionTabRole)

        if gVar.appSettings.showSwitchTab and not self._forceVisitItem and tabPos != -1:
            tabIcon = QIcon(':/icons/menu/tab.svg')
            iconRect = QRect(linkRect)
            iconRect.setX(iconRect.x())
            iconRect.setWidth(16)
            painter.drawPixmap(iconRect, tabIcon.pixmap(iconRect.size(), iconMode))

            textRect = QRect(linkRect)
            textRect.setX(textRect.x() + self._padding + 16 + self._padding)
            self.viewItemDrawText(painter, opt, textRect, _('Switch to tab'),
                    textPalette.color(colorLinkRole))
        elif isVisitSearchItem or isSearchSuggestion:
            self.viewItemDrawText(painter, opt, linkRect, link, textPalette.color(colorLinkRole))
        else:
            self.viewItemDrawText(painter, opt, linkRect, link, textPalette.color(colorLinkRole),
                    searchText)

    # override
    def sizeHint(self, option, index):
        '''
        @param option QStyleOptionViewItem
        @param index QModelIndex
        @return: QSize
        '''
        if not self._rowHeight:
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)

            w = opt.widget
            if w:
                style = w.style()
            else:
                style = QApplication.style()
            padding = style.pixelMetric(QStyle.PM_FocusFrameHMargin, None) + 1

            self._padding = max(padding, 3)
            self._rowHeight = 4 * self._padding + max(16, opt.fontMetrics.height())

        return QSize(200, self._rowHeight)

    def setForceVisitItem(self, enable):
        '''
        @param enable bool
        '''
        self._forceVisitItem = enable

    @classmethod
    def _s_viewItemDrawText(cls, textLayout, lineWidth):
        '''
        @param: textLayout QTextLayout
        @param: lineWidth int
        @return: QSizeF
        '''
        # qreal
        height = 0
        widthUsed = 0
        textLayout.beginLayout()
        # QTextLine
        line = textLayout.createLine()
        if line.isValid():
            line.setLineWidth(lineWidth)
            line.setPosition(QPointF(0, height))
            height += line.height()
            widthUsed = max(widthUsed, line.naturalTextWidth())

        textLayout.endLayout()
        return QSizeF(widthUsed, height)

    # private:
    def viewItemDrawText(self, painter, option, rect, text, color, searchText=''):  # noqa C901
        '''
        @note: most of codes taken from QCommonStylePrivate::viewItemDrawText
            added highlighting and simplified for single-line textlayouts
        @param painter QPainter
        @param option QStyleOptionViewItem
        @param rect QRect
        @param text QString
        @param color QColor
        @param searchText QString
        @return: int
        '''
        if not text:
            return 0

        fontMetrics = QFontMetrics(painter.font())
        elidedText = fontMetrics.elidedText(text, option.textElideMode, rect.width())
        textOption = QTextOption()
        textOption.setWrapMode(QTextOption.NoWrap)
        textOption.setAlignment(QStyle.visualAlignment(textOption.textDirection(),
            option.displayAlignment))
        textLayout = QTextLayout()
        textLayout.setFont(painter.font())
        textLayout.setText(elidedText)
        textLayout.setTextOption(textOption)

        if searchText:
            # QList<int>
            delimiters = []
            searchStrings = [ item.strip() for item in searchText.split(' ') ]
            searchStrings = [ item for item in searchStrings if item ]
            # Look for longer parts first
            searchStrings.sort(key=lambda x: len(x), reverse=True)

            text0 = text.lower()
            for string in searchStrings:
                string0 = string.lower()
                delimiter = text0.find(string0)

                while delimiter != -1:
                    start = delimiter
                    end = delimiter + len(string)
                    alreadyContains = False
                    for idx in range(0, len(delimiters), 2):
                        dStart = delimiters[idx]
                        dEnd = delimiters[idx+1]

                        if dStart <= start and dEnd >= end:
                            alreadyContains = True
                            break

                    if not alreadyContains:
                        delimiters.append(start)
                        delimiters.append(end)

                    delimiter = text0.find(string0, end)

            # We need to sort delimiters to properly paint all parts that user typed
            delimiters.sort()

            # If we don't find any match, just paint it withoutany highlight
            if delimiters and len(delimiters) % 2 == 0:
                highlightParts = []  # QList<QTextLayout::FormatRange>

                while delimiters:
                    highlightedPart = QTextLayout.FormatRange()
                    start = delimiters.pop(0)
                    end = delimiters.pop(0)
                    highlightedPart.start = start
                    highlightedPart.length = end - start
                    highlightedPart.format.setFontWeight(QFont.Bold)
                    highlightedPart.format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
                    highlightParts.append(highlightedPart)

                textLayout.setAdditionalFormats(highlightParts)

        # do layout
        self._s_viewItemDrawText(textLayout, rect.width())

        if textLayout.lineCount() <= 0:
            return 0

        textLine = textLayout.lineAt(0)

        # if elidedText after highlighting is longer than available width then
        # re-elide it and redo layout
        diff = textLine.naturalTextWidth() - rect.width()
        if diff > 0:
            # TODO: ?
            elidedText = fontMetrics.elidedText(elidedText, option.textElideMode,
                    rect.width() - diff)
            textLayout.setText(elidedText)
            # redo layout
            self._s_viewItemDrawText(textLayout, rect.width())

            if textLayout.lineCount() <= 0:
                return 0
            textLine = textLayout.lineAt(0)

        # draw line
        painter.setPen(color)
        # qreal
        width = max(rect.width(), textLayout.lineAt(0).width())
        # QRect
        layoutRect = QStyle.alignedRect(option.direction, option.displayAlignment,
                QSize(int(width), int(textLine.height())), rect)
        # QPointF
        position = layoutRect.topLeft()

        textLine.draw(painter, position)

        return int(min(rect.width(), textLayout.lineAt(0).naturalTextWidth()))
