from PyQt5.Qt import QStyledItemDelegate

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
    def paint(self, painter, option, index):
        '''
        @param painter QPainter
        @param option index QStyleOptionViewItem
        @param option index QModelIndex
        '''
        pass

    # override
    def sizeHint(self, option, index):
        '''
        @param option QStyleOptionViewItem
        @param index QModelIndex
        @return: QSize
        '''
        pass

    def setForceVisitItem(self, enable):
        '''
        @param enable bool
        '''
        pass

    # private:
    def viewItemDrawText(self, painter, option, rect, text, color, searchText=''):
        '''
        @param painter QPainter
        @param option QStyleOptionViewItem
        @param rect QRect
        @param text QString
        @param color QColor
        @param searchText QString
        @return: int
        '''
        pass
