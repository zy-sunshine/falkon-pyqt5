from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QStyleOptionViewItem
from PyQt5.Qt import QApplication
from PyQt5.Qt import QStyle
from PyQt5.Qt import QPalette
from PyQt5.Qt import Qt
from PyQt5.Qt import QRect
from PyQt5.Qt import QSize
from mc.common import const

class ListItemDelegate(QStyledItemDelegate):
    def __init__(self, iconSize, parent):
        super().__init__(parent)
        self._iconSize = iconSize
        self._updateParentHeight = False
        self._uniformItemSizes = False

        self._itemHeight = 0
        self._itemWidth = 0
        self._padding = 0

    def setUpdateParentHeight(self, update):
        self._updateParentHeight = update

    def setUniformItemSizes(self, uniform):
        self._uniformItemSizes = uniform

    def itemHeight(self):
        return self._itemHeight

    # override
    def paint(self, painter, option, index):
        '''
        @param: painter QPainter
        @param: option QStyleOptionViewItem
        @param: index QModelIndex
        '''
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        w = opt.widget
        # QStyle
        style = None
        # Qt::LayoutDirection
        direction = None
        if w:
            style = w.style()
            direction = w.layoutDirection()
        else:
            style = QApplication.style()
            direction = QApplication.layoutDirection()

        # QPalette.ColorRole
        colorRole = None
        if opt.state & QStyle.State_Selected:
            colorRole = QPalette.HighlightedText
        else:
            colorRole = QPalette.Text

        # QPalette.ColorGroup
        colorGroup = None
        if opt.state & QStyle.State_Enabled:
            if not (opt.state & QStyle.State_Active):
                colorGroup = QPalette.Inactive
            else:
                colorGroup = QPalette.Normal
        else:
            colorGroup = QPalette.Disabled

        if const.OS_WIN:
            opt.palette.setColor(QPalette.All, QPalette.HighlightedText,
                    opt.palette.color(QPalette.Active, QPalette.Text))
            opt.palette.setColor(QPalette.All, QPalette.Highlight,
                    opt.palette.base().color().darker(108))

        textPalette = opt.palette
        textPalette.setCurrentColorGroup(colorGroup)

        topPosition = opt.rect.top() + self._padding

        # Draw background
        opt.showDecorationSelected = True
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, opt, painter, w)

        # Draw icon
        iconRect = QRect(opt.rect.left() + (opt.rect.width() - self._iconSize) / 2,
                topPosition, self._iconSize, self._iconSize)
        visualIconRect = style.visualRect(direction, opt.rect, iconRect)
        pixmap = index.data(Qt.DecorationRole).pixmap(self._iconSize)
        painter.drawPixmap(visualIconRect, pixmap)
        topPosition += self._iconSize + self._padding

        # Draw title
        title = index.data(Qt.DisplayRole)
        leftTitleEdge = opt.rect.left() + self._padding
        titleRect = QRect(leftTitleEdge, topPosition, opt.rect.width() - 2 * self._padding,
                opt.fontMetrics.height())
        visualTitleRect = style.visualRect(direction, opt.rect, titleRect)
        style.drawItemText(painter, visualTitleRect, Qt.AlignCenter, textPalette,
                True, title, colorRole)

    # override
    def sizeHint(self, option, index):
        '''
        @param: option QStyleOptionViewItem
        @param: index QModelIndex
        '''
        if not self._itemHeight:
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)

            w = opt.widget
            # QStyle
            style = None
            if w:
                style = w.style()
            else:
                style = QApplication.style()
            padding = style.pixelMetric(QStyle.PM_FocusFrameHMargin, None) + 1

            self._padding = max(5, padding)

            self._itemHeight = 3 * self._padding + opt.fontMetrics.height() + self._iconSize

            # update height of parent widget
            p = self.parent()
            if p and self._updateParentHeight:
                frameWidth = p.style().pixelMetric(QStyle.PM_DefaultFrameWidth, None, p)
                p.setFixedHeight(self._itemHeight + 2 * frameWidth)

        width = 2 * self._padding + option.fontMetrics.width(index.data(Qt.DisplayRole))
        width = max(self._iconSize + 2 * self._padding, width)

        if self._uniformItemSizes:
            if width > self._itemWidth:
                self._itemWidth = width
            else:
                width = self._itemWidth

        return QSize(width, self._itemHeight)
