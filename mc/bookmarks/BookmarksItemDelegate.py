from PyQt5.Qt import QStyledItemDelegate
from PyQt5.Qt import QRect
from mc.bookmarks.BookmarksModel import BookmarksModel
from mc.bookmarks.BookmarkItem import BookmarkItem
from PyQt5.Qt import QStyleOption
from PyQt5.Qt import QStyle
from PyQt5.Qt import QApplication

class BookmarksItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        '''
        @param: parent QTreeView
        '''
        super().__init__(parent)
        self._tree = parent # QTreeView
        self._lastRect = QRect()

    # override
    def paint(self, painter, option, index):
        '''
        @param: painter QPainter
        @param: option QStyleOptionViewItem
        @param: index QModelIndex
        '''
        super().paint(painter, option, index)

        if index.data(BookmarksModel.TypeRole) == BookmarkItem.Separator:
            opt = QStyleOption(option)
            opt.state &= ~QStyle.State_Horizontal

            # We need to fake continuous line over 2 columns
            if self._tree.model().columnCount(index) == 2:
                if index.column() == 1:
                    opt.rect = self._lastRect
                else:
                    opt.rect.setWidth(opt.rect.width() + self._tree.columnWidth(1))
                    self._lastRect = opt.rect
            QApplication.style().drawPrimitive(QStyle.PE_IndicatorToolBarSeparator, opt, painter)
