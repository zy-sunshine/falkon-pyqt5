from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.Qt import QKeyEvent
from PyQt5.Qt import Qt
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import QShortcut
from mc.webengine.WebPage import WebPage

class SearchToolBar(QWidget):
    def __init__(self, view, parent=None):
        '''
        @param: view WebView
        @param: parent QWidget
        '''
        super().__init__(parent)
        self._ui = uic.loadUi('mc/webtab/SearchToolBar.ui', self)
        self._view = view  # WebView
        self._findFlags = QWebEnginePage.FindCaseSensitively  # QWebEnginePage.FindFlags
        self._searchRequests = 0

        self._ui.closeButton.clicked.connect(self.close)
        self._ui.lineEdit.textEdited.connect(self.findNext)
        self._ui.next.clicked.connect(self.findNext)
        self._ui.previous.clicked.connect(self.findPrevious)
        self._ui.caseSensitive.clicked.connect(self.caseSensitivityChanged)

        findNextAction = QShortcut(QKeySequence('F3'), self)
        findNextAction.activated.connect(self.findNext)

        findPreviousAction = QShortcut(QKeySequence('Shift+F3'), self)
        findPreviousAction.activated.connect(self.findPrevious)

        parent.installEventFilter(self)

    def showMinimalInPopupWindow(self):
        # Show only essentials widget + set minimum width
        self._ui.caseSensitive.hide()
        self._ui.horizontalLayout.setSpacing(2)
        self._ui.horizontalLayout.setContentsMargins(2, 6, 2, 6)
        self.setMinimumWidth(260)

    def focusSearchLine(self):
        self._ui.lineEdit.setFocus()

    # override
    def eventFilter(self, obj, event):
        '''
        @param: obj QObject
        @param: event QEvent
        '''
        if event.type() == QKeyEvent.KeyPress:
            evtKey = event.key()
            if evtKey == Qt.Key_Escape:
                self.close()
            elif evtKey in (Qt.Key_Enter, Qt.Key_Return):
                if event.modifiers() & Qt.ShiftModifier:
                    self.findPrevious()
                else:
                    self.findNext()
        return False

    # public Q_SLOTS:
    def setText(self, text):
        self._ui.lineEdit.setText(text)

    def searchText(self, text):
        self._searchRequests += 1
        guard = self  # QPointer<SearchToolBar>

        def findCb(found):
            if not guard:  # TODO: check py C++ pointer exists
                return
            self._searchRequests -= 1
            if self._searchRequests != 0:
                return
            if not self._ui.lineEdit.text():
                found = True

            self._ui.lineEdit.setProperty('notfound', not found)
            self._ui.lineEdit.style().unpolish(self._ui.lineEdit)
            self._ui.lineEdit.style().polish(self._ui.lineEdit)

            # Clear selection
            self._view.page().runJavaScript('window.getSelection().empty();',
                    WebPage.SafeJsWorld)

        self._view.findText(text, QWebEnginePage.FindFlag(self._findFlags), findCb)

    def updateFindFlags(self):
        if self._ui.caseSensitive.isChecked():
            self._findFlags |= QWebEnginePage.FindCaseSensitively
        else:
            self._findFlags &= ~QWebEnginePage.FindCaseSensitively

    def caseSensitivityChanged(self):
        self.updateFindFlags()

        self.searchText('')
        self.searchText(self._ui.lineEdit.text())

    def findNext(self):
        self._findFlags = QWebEnginePage.FindCaseSensitively
        self.updateFindFlags()

        self.searchText(self._ui.lineEdit.text())

    def findPrevious(self):
        self._findFlags = QWebEnginePage.FindBackward
        self.updateFindFlags()

        self.searchText(self._ui.lineEdit.text())

    def close(self):
        self.hide()
        self.searchText('')
        self._view.setFocus()
        self.deleteLater()
