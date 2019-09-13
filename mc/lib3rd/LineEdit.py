from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import Qt
from PyQt5.Qt import QEvent
from PyQt5.Qt import QHBoxLayout
from PyQt5.Qt import QBoxLayout
from PyQt5.Qt import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.Qt import QIcon
from PyQt5.Qt import QAction
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QApplication
from PyQt5.Qt import QInputMethodEvent
from PyQt5.Qt import QMouseEvent
from PyQt5.QtWidgets import QMenu
from mc.common.globalvars import gVar

class SideWidget(QWidget):
    # Q_SIGNALS:
    sizeHintChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.ArrowCursor)
        self.setFocusPolicy(Qt.ClickFocus)

    # protected:
    # override
    def event(self, event):
        '''
        @param: event QEvent
        '''
        evtType = event.type()
        if evtType == QEvent.LayoutRequest:
            self.sizeHintChanged.emit()
        elif evtType in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                QEvent.MouseButtonDblClick, QEvent.MouseMove):
            event.accept()
            return True
        return super().event(event)

class LineEdit(QLineEdit):
    '''
    @note: LineEdit is a subclass of QLineEdit that provides an easy and simple
    way to add widgets on the left or right hand side of the text

    The layout of the widgets on either side are handled by a QHBoxLayout.
    You can set the spacing around the widgets with setWidgetSpacing().

    As widgets are added to the class they are inserted from the outside
    into the center of the widget.
    '''

    # enum WidgetPosition
    LeftSide = 0
    RightSide = 1

    # enum EditAction
    Undo = 0
    Redo = 1
    Cut = 2
    Copy = 3
    Paste = 4
    PasteAndGo = 5
    Delete = 6
    ClearAll = 7
    SelectAll = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._leftWidget = None  # SideWidget
        self._rightWidget = None  # SideWidget
        self._leftLayout = None  # QHBoxLayout
        self._rightLayout = None  # QHBoxLayout
        self._mainLayout = None  # QHBoxLayout
        self._editActions = [None] * 9  # QAction[9]

        self._minHeight = 0
        self._leftMargin = -1
        self._ignoreMousePress = False

        self._init()

    # private:
    def _init(self):
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(0)

        self._leftWidget = SideWidget(self)
        self._leftWidget.resize(0, 0)
        self._leftLayout = QHBoxLayout(self._leftWidget)
        self._leftLayout.setContentsMargins(0, 0, 0, 0)
        if self.isRightToLeft():
            direction = QBoxLayout.RightToLeft
        else:
            direction = QBoxLayout.LeftToRight
        self._leftLayout.setDirection(direction)

        self._rightWidget = SideWidget(self)
        self._rightWidget.resize(0, 0)
        self._rightLayout = QHBoxLayout(self._rightWidget)
        self._rightLayout.setContentsMargins(0, 0, 2, 0)
        self._rightLayout.setDirection(direction)

        self._mainLayout.addWidget(self._leftWidget, 0, Qt.AlignVCenter | Qt.AlignLeft)
        self._mainLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self._mainLayout.addWidget(self._rightWidget, 0, Qt.AlignVCenter | Qt.AlignRight)
        self._mainLayout.setDirection(direction)

        self.setWidgetSpacing(3)

        self._leftWidget.sizeHintChanged.connect(self.updateTextMargins)
        self._rightWidget.sizeHintChanged.connect(self.updateTextMargins)

        undoAction = QAction(QIcon.fromTheme('edit-undo'), _('&Undo'), self)
        undoAction.setShortcut(QKeySequence('Ctrl+Z'))
        undoAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        undoAction.triggered.connect(self.undo)

        redoAction = QAction(QIcon.fromTheme('edit-redo'), _('&Redo'), self)
        redoAction.setShortcut(QKeySequence('Ctrl+Shift+Z'))
        redoAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        redoAction.triggered.connect(self.redo)

        cutAction = QAction(QIcon.fromTheme('edit-cut'), _('Cu&t'), self)
        cutAction.setShortcut(QKeySequence('Ctrl+X'))
        cutAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        cutAction.triggered.connect(self.cut)

        copyAction = QAction(QIcon.fromTheme('edit-copy'), _('&Copy'), self)
        copyAction.setShortcut(QKeySequence('Ctrl+C'))
        copyAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        copyAction.triggered.connect(self.copy)

        pasteAction = QAction(QIcon.fromTheme('edit-paste'), _('&Paste'), self)
        pasteAction.setShortcut(QKeySequence('Ctrl+V'))
        pasteAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        pasteAction.triggered.connect(self.paste)

        pasteAndGoAction = QAction(self)
        pasteAndGoAction.setShortcut(QKeySequence('Ctrl+Shift+V'))
        pasteAndGoAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)

        deleteAction = QAction(QIcon.fromTheme('edit-delete'), _('Delete'), self)
        deleteAction.triggered.connect(self._slotDelete)

        clearAllAction = QAction(QIcon.fromTheme('edit-clear'), _('Clear All'), self)
        clearAllAction.triggered.connect(self.clear)

        selectAllAction = QAction(QIcon.fromTheme('edit-select-all'), _('Select All'), self)
        selectAllAction.setShortcut(QKeySequence('Ctrl+A'))
        selectAllAction.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        selectAllAction.triggered.connect(self.selectAll)

        self._editActions[self.Undo] = undoAction
        self._editActions[self.Redo] = redoAction
        self._editActions[self.Cut] = cutAction
        self._editActions[self.Copy] = copyAction
        self._editActions[self.Paste] = pasteAction
        self._editActions[self.PasteAndGo] = pasteAndGoAction
        self._editActions[self.Delete] = deleteAction
        self._editActions[self.ClearAll] = clearAllAction
        self._editActions[self.SelectAll] = selectAllAction

        # Make action shortcuts available for webview
        self.addAction(undoAction)
        self.addAction(redoAction)
        self.addAction(cutAction)
        self.addAction(copyAction)
        self.addAction(pasteAction)
        self.addAction(pasteAndGoAction)
        self.addAction(deleteAction)
        self.addAction(clearAllAction)
        self.addAction(selectAllAction)

        # Connections to update edit actions
        self.textChanged.connect(self._updateActions)
        self.selectionChanged.connect(self._updateActions)

        self._updateActions()

    def addWidget(self, widget, position):
        '''
        @param: widget QWidget
        @param: position WidgetPosition
        '''
        if not widget:
            return
        if position == self.LeftSide:
            self._leftLayout.addWidget(widget)
        else:
            self._rightLayout.addWidget(widget)

    def removeWidget(self, widget):
        '''
        @param: widget QWidget
        '''
        if not widget:
            return

        self._leftLayout.removeWidget(widget)
        self._rightLayout.removeWidget(widget)
        widget.hide()

    def setWidgetSpacing(self, spacing):
        self._leftLayout.setSpacing(spacing)
        self._rightLayout.setSpacing(spacing)
        self.updateTextMargins()

    def widgetSpacing(self):
        '''
        @return: int
        '''
        return self._leftLayout.spacing()

    def leftMargin(self):
        '''
        @return: int
        '''
        return self._leftMargin

    def setTextFormat(self, format_):
        '''
        @param: format_ QList<QTextLayout::FormatRange>
        @note: http://stackoverflow.com/a/14424003
        '''
        attributes = []  # QList<QInputMethodEvent::Attribute>

        for fr in format_:
            type_ = QInputMethodEvent.TextFormat
            start = fr.start - self.currentPosition()
            length = fr.length
            value = fr.format
            attributes.append(QInputMethodEvent.Attribute(type_, start, length, value))

        ev = QInputMethodEvent('', attributes)
        self.event(ev)

    def clearTextFormat(self):
        self.setTextFormat([])

    def minHeight(self):
        return self._minHeight

    def setMinHeight(self, height):
        self._minHeight = height

    # override
    def sizeHint(self):
        '''
        @return: QSize
        '''
        s = super().sizeHint()

        if s.height() < self._minHeight:
            s.setHeight(self._minHeight)

        return s

    def editAction(self, action):
        '''
        @param: action EditAction
        @return: QAction
        '''
        return self._editActions[action]

    # public Q_SLOTS:
    def setLeftMargin(self, margin):
        '''
        @param: margin int
        '''
        self._leftMargin = margin

    def updateTextMargins(self):
        left = self._leftWidget.sizeHint().width()
        right = self._rightWidget.sizeHint().width()
        top = 0
        bottom = 0

        if self._leftMargin >= 0:
            left = self._leftMargin

        self.setTextMargins(left, top, right, bottom)

    # protected:
    # override
    def focusInEvent(self, event):
        '''
        @param: event QFocusEvent
        '''
        if event.reason() == Qt.MouseFocusReason and gVar.appSettings.selectAllOnClick:
            self._ignoreMousePress = True
            self.selectAll()

        super().focusInEvent(event)

    # override
    def mousePressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if self._ignoreMousePress:
            self._ignoreMousePress = False
            return

        super().mousePressEvent(event)

    # override
    def mouseReleaseEvent(self, event):
        '''
        @note: Workaround issue in QLineEdit::setDragEnabled(True)
        It will incorrectly set cursor position at the end
        of selection when clicking (and not dragging) into selected text
        @param: event QMouseEvent
        '''
        if not self.dragEnabled():
            super().mouseReleaseEvent(event)
            return

        wasSelectedText = not not self.selectedText()

        super().mouseReleaseEvent(event)

        isSelectedText = not not self.selectedText()

        if wasSelectedText and not isSelectedText:
            ev = QMouseEvent(QEvent.MouseButtonPress, event.pos(), event.button(),
                    event.buttons(), event.modifiers())
            self.mousePressEvent(ev)

    # override
    def mouseDoubleClickEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        if event.buttons() == Qt.LeftButton and gVar.appSettings.selectAllOnDoubleClick:
            self.selectAll()
            return

        super().mouseDoubleClickEvent(event)

    # override
    def resizeEvent(self, event):
        '''
        @param: event QResizeEvent
        '''
        super().resizeEvent(event)

        self._leftWidget.setFixedHeight(self.height())
        self._rightWidget.setFixedHeight(self.height())

    # override
    def event(self, event):
        '''
        @param: event QEvent
        @return: bool
        '''
        if event.type() == QEvent.LayoutDirectionChange:
            # By this we undo reversing of layout when direction is RTL.
            if self.isRightToLeft():
                self._mainLayout.setDirection(QBoxLayout.RightToLeft)
                self._leftLayout.setDirection(QBoxLayout.RightToLeft)
                self._rightLayout.setDirection(QBoxLayout.RightToLeft)
            else:
                self._mainLayout.setDirection(QBoxLayout.LeftToRight)
                self._leftLayout.setDirection(QBoxLayout.LeftToRight)
                self._rightLayout.setDirection(QBoxLayout.LeftToRight)
        return super().event(event)

    def _createContextMenu(self):
        '''
        @note: Modified QLineEdit.createStandardContextMenu to support icon and PasteAndGo action
        @return: QMenu
        '''
        popup = QMenu(self)
        popup.setObjectName('qt_edit_menu')

        if not self.isReadOnly():
            popup.addAction(self._editActions[self.Undo])
            popup.addAction(self._editActions[self.Redo])
            popup.addSeparator()
            popup.addAction(self._editActions[self.Cut])

        popup.addAction(self._editActions[self.Copy])

        if not self.isReadOnly():
            self._updatePasteActions()
            popup.addAction(self._editActions[self.Paste])
            if self._editActions[self.PasteAndGo].text():
                popup.addAction(self._editActions[self.PasteAndGo])
            popup.addAction(self._editActions[self.Delete])
            popup.addAction(self._editActions[self.ClearAll])

        popup.addSeparator()
        popup.addAction(self._editActions[self.SelectAll])

        # TODO:
        # Hack to get QUnicodeControlCharactorMenu
        # QMenu tmp
        tmp = self.createStandardContextMenu()
        tmp.setParent(popup)
        tmp.hide()
        if not tmp.actions().isEmpty():
            lastAction = tmp.actions().constLast()
        else:
            lastAction = 0

        if lastAction and lastAction.menu() and lastAction.menu().inherits('QUnicodeControlCharacterMenu'):
            popup.addAction(lastAction)

        return popup

    # private Q_SLOTS:
    def _updateActions(self):
        self._editActions[self.Undo].setEnabled(not self.isReadOnly() and self.isUndoAvailable())
        self._editActions[self.Redo].setEnabled(not self.isReadOnly() and self.isRedoAvailable())
        self._editActions[self.Cut].setEnabled(not self.isReadOnly() and self.hasSelectedText() and
                self.echoMode() == QLineEdit.Normal)
        self._editActions[self.Copy].setEnabled(self.hasSelectedText() and self.echoMode() == QLineEdit.Normal)
        self._editActions[self.Delete].setEnabled(not self.isReadOnly() and self.hasSelectedText())
        self._editActions[self.SelectAll].setEnabled(not not self.text() and self.selectedText() != self.text())
        self._editActions[self.Paste].setEnabled(True)
        self._editActions[self.PasteAndGo].setEnabled(True)

    def _updatePasteActions(self):
        '''
        @note: Paste actions are updated in separate slot because accessing clipboard is expensive
        '''
        pasteEnabled = not self.isReadOnly() and QApplication.clipboard().text()

        self._editActions[self.Paste].setEnabled(pasteEnabled)
        self._editActions[self.PasteAndGo].setEnabled(pasteEnabled)

    def _slotDelete(self):
        if self.hasSelectedText():
            self.del_()
