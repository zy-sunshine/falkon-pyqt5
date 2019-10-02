from PyQt5.Qt import QPoint
from PyQt5.Qt import Qt
from PyQt5.Qt import QApplication
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QDrag
from PyQt5.Qt import QMimeData
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu

class SqueezeLabelV2(QLabel):
    def __init__(self, *args, **kwargs):
        '''
        @param: parent QWidget
        @param: string QString
        '''
        if args and isinstance(args[0], str):
            self.setText(args[0])
            super().__init__()
        elif args and isinstance(args[0], QWidget):
            super().__init__(args[0])
        else:
            super().__init__(None)

        self._originalText = ''
        self._dragStart = QPoint()

    def originalText(self):
        return self._originalText

    def setText(self, txt):
        self._originalText = txt
        # QFontMetrics
        fm = self.fontMetrics()
        elided = fm.elidedText(self._originalText, Qt.ElideMiddle, self.width())
        super().setText(elided)

    # private Q_SLOTS:
    def _copy(self):
        if len(self.selectedText()) == len(self.text()):
            QApplication.clipboard().setText(self._originalText)
        else:
            QApplication.clipboard().setText(self.selectedText())

    # protected:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        if not (self.textInteractionFlags() & Qt.TextSelectableByMouse) and \
                not (self.textInteractionFlags() & Qt.TextSelectableByKeyboard):
            event.ignore()
            return

        menu = QMenu()
        act = menu.addAction(_('Copy'), self._copy)
        act.setShortcut(QKeySequence('Ctrl+C'))
        act.setEnabled(self.hasSelectedText())

        menu.exec_(event.globalPos())

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QKeyEvent
        '''
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self._copy()

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super().resizeEvent(event)
        # QFontMetrics
        fm = self.fontMetrics()
        elided = fm.elidedText(self._originalText, Qt.ElideMiddle, self.width())
        self.setText(elided)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if event.buttons() & Qt.LeftButton:
            self._dragStart = event.pos()

        super().mousePressEvent(event)

    # override
    def mouseMoveEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if not (event.buttons() & Qt.LeftButton) or len(self.selectedText()) != len(self.text()):
            super().mouseMoveEvent(event)
            return

        manhattanLength = (event.pos() - self._dragStart).manhattanLength()
        if manhattanLength <= QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self._originalText)

        drag.setMimeData(mime)
        drag.exec_()
