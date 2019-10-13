from PyQt5.Qt import QColor
from PyQt5.Qt import QUrl
from PyQt5.Qt import QStringListModel
from PyQt5.Qt import QCompleter
from PyQt5.Qt import QTimer
from PyQt5.Qt import QStyle
from PyQt5.Qt import QStyleOptionFrame
from PyQt5.Qt import QPalette
from PyQt5.Qt import QPainter
from PyQt5.Qt import QBrush
from PyQt5.Qt import QPen
from PyQt5.Qt import QRect
from PyQt5.Qt import Qt
from PyQt5.Qt import QTextLayout
from PyQt5.Qt import QTextCharFormat
from PyQt5.Qt import QIcon
from PyQt5.Qt import QFocusEvent
from mc.webengine.WebPage import WebPage
from mc.webengine.LoadRequest import LoadRequest
from mc.webengine.WebView import WebView
from mc.opensearch.SearchEnginesManager import SearchEngine
from mc.lib3rd.LineEdit import LineEdit
from mc.tools.IconProvider import IconProvider
from mc.common.globalvars import gVar
from mc.bookmarks.BookmarksIcon import BookmarksIcon
from mc.autofill.AutoFillIcon import AutoFillIcon
from mc.tools.Colors import Colors
from mc.app.Settings import Settings
from .GoIcon import GoIcon
from .SiteIcon import SiteIcon
from .DownIcon import DownIcon
from .completer.LocationCompleter import LocationCompleter

class LocationBar(LineEdit):

    # ProgressStyle
    _ProgressFilled = 0
    _ProgressBottom = 1
    _ProgressTop = 2

    class LoadAction:
        # enum Type
        Invalid = 0
        Search = 1
        Bookmark = 2
        Url = 3
        def __init__(self):
            self.type = self.Invalid
            self.searchEngine = SearchEngine()
            self.bookmark = None  # BookmarkItem
            self.loadRequest = LoadRequest()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._completer = None  # LocationCompleter
        self._domainCompleterModel = None  # QStringListModel

        self._bookmarkIcon = None  # BookmarksIcon
        self._goIcon = None  # GoIcon
        self._siteIcon = None  # SiteIcon
        self._autofillIcon = None  # AutoFillIcon

        self._window = None  # BrowserWindow
        self._webView = None  # TabbedWebView

        self._holdingAlt = False
        self._oldTextLength = 0
        self._currentTextLength = 0

        self._loadProgress = 0
        self._progressVisible = True
        self._progressStyle = 0  # ProgressStyle
        self._progressColor = QColor()
        self._progressTimer = None  # QTimer

        self.setObjectName('locationbar')
        self.setDragEnabled(True)

        # Disable KDE QLineEdit transitions, it breaks with setText() && home()
        self._bookmarkIcon = BookmarksIcon(self)
        self._goIcon = GoIcon(self)
        self._siteIcon = SiteIcon(self)
        self._autofillIcon = AutoFillIcon(self)
        down = DownIcon(self)

        self.addWidget(self._siteIcon, LineEdit.LeftSide)
        self.addWidget(self._autofillIcon, LineEdit.RightSide)
        self.addWidget(self._bookmarkIcon, LineEdit.RightSide)
        self.addWidget(self._goIcon, LineEdit.RightSide)
        self.addWidget(down, LineEdit.RightSide)

        self._completer = LocationCompleter(self)
        self._completer.setLocationBar(self)
        self._completer.showCompletion.connect(self._showCompletion)
        self._completer.showDomainCompletion.connect(self._showDomainCompletion)
        self._completer.clearCompletion.connect(self._clearCompletion)
        self._completer.loadRequested.connect(self.loadRequest)
        self._completer.popupClosed.connect(self._updateSiteIcon)

        self._domainCompleterModel = QStringListModel(self)
        domainCompleter = QCompleter(self)
        domainCompleter.setCompletionMode(QCompleter.InlineCompletion)
        domainCompleter.setModel(self._domainCompleterModel)
        self.setCompleter(domainCompleter)

        self._progressTimer = QTimer(self)
        self._progressTimer.setInterval(700)
        self._progressTimer.setSingleShot(True)
        self._progressTimer.timeout.connect(self._hideProgress)

        self.editAction(self.PasteAndGo).setText(_('Paste And &Go'))
        self.editAction(self.PasteAndGo).setIcon(QIcon.fromTheme('edit-paste'))
        self.editAction(self.PasteAndGo).triggered.connect(self._pasteAndGo)

        self.textEdited.connect(self._textEdited)
        self._goIcon.clicked.connect(self._requestLoadUrl)
        down.clicked.connect(self._completer.showMostVisited)
        # TODO:
        #gVar.app.searchEnginesManager().activeEngineChanged.connect(self._updatePlaceHolderText)
        #gVar.app.searchEnginesManager().defaultEngineChanged.connect(self._updatePlaceHolderText)

        self._loadSettings()

        self._updateSiteIcon()

        # Hide icons by default
        self._goIcon.setVisible(gVar.appSettings.alwaysShowGoIcon)
        self._autofillIcon.hide()

        QTimer.singleShot(0, self._updatePlaceHolderText)

    def browserWindow(self):
        '''
        @note: BrowserWindow can be null!
        @return: BrowserWindow
        '''
        return self._window

    def setBrowserWindow(self, window):
        self._window = window
        self._completer.setMainWindow(self._window)
        self._siteIcon.setBrowserWindow(self._window)

    def webView(self):
        '''
        @return TabbedWebView
        '''
        return self._webView

    def setWebView(self, view):
        '''
        @param: view TabbedWebView -> WebView -> QWebEngineView
        '''
        self._webView = view

        self._bookmarkIcon.setWebView(self._webView)
        self._siteIcon.setWebView(self._webView)
        self._autofillIcon.setWebView(self._webView)

        self._webView.loadStarted.connect(self._loadStarted)
        self._webView.loadProgress.connect(self.__loadProgress)
        self._webView.loadFinished.connect(self._loadFinished)
        self._webView.urlChanged.connect(self.showUrl)
        self._webView.privacyChanged.connect(self._setPrivacyState)

    @classmethod
    def convertUrlToText(cls, url):
        '''
        @note: It was most probably entered by user, so don't urlencode it Also don't urlencode JavaScript code
        @param: url QUrl
        @return: QString
        '''
        if not url.scheme() or url.scheme() == 'javascript':
            return QUrl.fromPercentEncoding(url.toEncoded())

        stringUrl = gVar.appTools.urlEncodeQueryString(url)

        if stringUrl == 'app:speeddial' or stringUrl == 'about:blank':
            stringUrl = ''

        return stringUrl

    @classmethod
    def searchEngine(cls):
        '''
        @return: SearchEngine
        '''
        if not gVar.appSettings.searchFromAddressBar:
            return SearchEngine()
        elif gVar.appSettings.searchWithDefaultEngine:
            return gVar.app.searchEnginesManager().defaultEngine()
        else:
            return gVar.app.searchEnginesManager().activeEngine()

    @classmethod
    def loadAction(cls, text):
        '''
        @return: LoadAction
        '''
        action = cls.LoadAction()

        t = text.strip()
        if not t:
            return action

        # Check for Search Engine shortcut
        firstSpacePos = t.find(' ')
        if gVar.appSettings.searchFromAddressBar and firstSpacePos != -1:
            shortcut = t[:firstSpacePos]
            searchedString = t[firstSpacePos:].strip()

            en = gVar.app.searchEnginesManager().engineForShortcut(shortcut)
            if en.isValid():
                action.type = cls.LoadAction.Search
                action.searchEngine = en
                url = gVar.app.searchEnginesManager().searchResult(en, searchedString)
                action.loadRequest = LoadRequest(url)
                return action

        # Check for Bookmark keyword
        items = gVar.app.bookmarks().searchKeyword(t)
        if items:
            item = items[0]
            action.type = cls.LoadAction.Bookmark
            action.bookmark = item
            action.loadRequest.setUrl(item.url())
            return action

        if not gVar.appSettings.searchFromAddressBar:
            guessedUrl = QUrl.fromUserInput(t)
            if guessedUrl.isValid():
                action.type = cls.LoadAction.Url
                action.loadRequest = LoadRequest(guessedUrl)
            return action

        # Check for one word search
        if t != 'localhost' \
                and gVar.appTools.containsSpace(t) \
                and '.' not in t \
                and ':' not in t \
                and '/' not in t:
            action.type = cls.LoadAction.Search
            action.searchEngine = cls.searchEngine()
            url = gVar.app.searchEnginesManager().searchResult(cls.searchEngine(), t)
            action.loadRequest = LoadRequest(url)
            return action

        # Otherwise load as url
        guessedUrl = QUrl.fromUserInput(t)
        if guessedUrl.isValid():
            # Always allow javascript: to be loaded
            forceLoad = guessedUrl.scheme() == 'javascript'
            # Only allow spaces in query
            urlRaw = guessedUrl.toString(QUrl.RemoveQuery)
            if forceLoad or not gVar.appTools.containsSpace(t) or \
                    not gVar.appTools.contiansSpace(urlRaw):
                # Only allow supported schemes
                if forceLoad or guessedUrl.scheme() in WebPage.supportedSchemes():
                    action.type = cls.LoadAction.Url
                    action.loadRequest = LoadRequest(guessedUrl)
                    return action

        # Search when creating url failed
        action.type = cls.LoadAction.Search
        action.searchEngine = cls.searchEngine()
        url = gVar.app.searchEnginesManager().searchResult(cls.searchEngine(), t)
        action.loadRequest = LoadRequest(url)
        return action

    # public Q_SLOTS
    def setText(self, text):
        # TODO: ?
        self._oldTextLength = len(text)
        self._currentTextLength = self._oldTextLength

        super().setText(text)

        self._refreshTextFormat()

    def showUrl(self, url):
        if self.hasFocus() or url.isEmpty():
            return

        stringUrl = self.convertUrlToText(url)

        if self.text() == stringUrl:
            self.home(False)
            self._refreshTextFormat()
            return

        # Set converted url as text
        self.setText(stringUrl)

        # Move cursor to the start
        self.home(False)

        self._bookmarkIcon.checkBookmark(url)

    def loadRequest(self, request):
        '''
        @param: request LoadRequest
        '''
        if not self._webView.webTab().isRestored():
            return

        urlString = self.convertUrlToText(request.url())

        self._completer.closePopup()
        self._webView.setFocus()

        if urlString != self.text():
            self.setText(urlString)

        self._webView.userLoadAction(request)

    # private Q_SLOTS
    def _textEdited(self, text):
        self._oldTextLength = self._currentTextLength
        self._currentTextLength = len(text)

        if text:
            self._completer.complete(text)
            icon = QIcon.fromTheme('edit-find', QIcon(':/icons/menu/search-icon.svg'))
            self._siteIcon.setIcon(icon)
        else:
            self._completer.closePopup()

        self._setGoIconVisible(True)

    def _requestLoadUrl(self):
        req = self.loadAction(self.text()).loadRequest
        self.loadRequest(req)
        self._updateSiteIcon()

    def _pasteAndGo(self):
        self.clear()
        self.paste()
        self._requestLoadUrl()

    def _updateSiteIcon(self):
        if self._completer.isVisible():
            self._siteIcon.setIcon(QIcon.fromTheme('edit-find',
                QIcon(':/icons/menu/search-icon.svg')))
        else:
            icon = IconProvider.emptyWebIcon()
            secured = self.property('secured')
            if secured:
                icon = QIcon.fromTheme('document-encrypted', icon)
            self._siteIcon.setIcon(icon.pixmap(16))

    def _updatePlaceHolderText(self):
        if gVar.appSettings.searchFromAddressBar:
            self.setPlaceholderText(_('Enter address or search with %s') % self.searchEngine().name)
        else:
            self.setPlaceholderText(_('Enter address'))

    def _setPrivacyState(self, state):
        '''
        @param: state bool
        '''
        self._siteIcon.setProperty('secured', state)
        self._siteIcon.style().unpolish(self._siteIcon)
        self._siteIcon.style().polish(self._siteIcon)

        self.setProperty('secured', state)
        self.style().unpolish(self)
        self.style().polish(self)

        self._updateSiteIcon()

    def _setGoIconVisible(self, state):
        '''
        @param: state bool
        '''
        if state:
            self._bookmarkIcon.hide()
            self._goIcon.show()
        else:
            self._bookmarkIcon.show()
            if not gVar.appSettings.alwaysShowGoIcon:
                self._goIcon.hide()

        self.updateTextMargins()

    def _showCompletion(self, completion, completeDomain):
        '''
        @param: completion QString
        @param: completeDomain bool
        '''
        super().setText(completion)

        # Move cursor to the end
        self.end(False)

        if completeDomain:
            self.completer().complete()

        self._updateSiteIcon()

    def _showDomainCompletion(self, completion):
        '''
        @param: completion QString
        '''
        self._domainCompleterModel.setStringList([completion])

        # We need to manually force the completion because model is updated
        # asynchronously, But only force completion when theuser actually added
        # new text
        if completion and self._oldTextLength < self._currentTextLength:
            self.completer().complete()

    def _clearCompletion(self):
        self._webView.setFocus()
        self.showUrl(self._webView.url())

    def _loadStarted(self):
        self._progressVisible = True
        self._progressTimer.start()
        self._autofillIcon.hide()

    def __loadProgress(self, progress):
        '''
        @param: progress int
        '''
        if gVar.appSettings.showLoadingProgress:
            self._loadProgress = progress
            self.update()

    def _loadFinished(self):
        if gVar.appSettings.showLoadingProgress:
            self._progressTimer.start()

        page = self._webView.page()
        if isinstance(page, WebPage) and page.autoFillUsernames():
            self._autofillIcon.setUsernames(page.autoFillUsernames())
            self._autofillIcon.show()

    def _hideProgress(self):
        if gVar.appSettings.showLoadingProgress:
            self._progressVisible = False
            self.update()

    def _loadSettings(self):
        settings = Settings()
        settings.beginGroup('AddressBar')
        self._progressStyle = settings.value('ProgressStyle', 0)
        customColor = settings.value('UseCustomProgressColor', False)
        if customColor:
            self._progressColor = settings.value('CustomProgressColor',
                    self.palette().color(QPalette.Highlight))
        else:
            self._progressColor = QColor()
        settings.endGroup()

    # private:
    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        menu = self._createContextMenu()
        menu.setAttribute(Qt.WA_DeleteOnClose)

        # Prevent choosing first option with double rightclick
        pos = event.globalPos()
        pos.setY(pos.y() + 1)
        menu.popup(pos)

    # override
    def showEvent(self, event):
        '''
        @param: event QShowEvent
        '''
        super().showEvent(event)

        self._refreshTextFormat()

    # override
    def focusInEvent(self, event):
        '''
        @param: event QFocusEvent
        '''
        if self._webView:
            stringUrl = self.convertUrlToText(self._webView.url())

            # Text has been edited, let's show go button
            if stringUrl != self.text():
                self._setGoIconVisible(True)

        self.clearTextFormat()
        super().focusInEvent(event)

        if self._window and Settings().value('Browser-View-Settings/instantBookmarksToolbar', type=bool):
            self._window.bookmarksToolbar().show()

    # override
    def focusOutEvent(self, event):
        '''
        @param: event QFocusEvent
        '''
        # Context menu or completer popup were opened
        # Let's block focusOutEvent to trick QLineEdit and point cursor properly
        if event.reason() == Qt.PopupFocusReason:  # TODO: ?
            return

        super().focusOutEvent(event)

        self._setGoIconVisible(False)

        if not self.text().strip():
            self.clear()

        self._refreshTextFormat()

        if self._window and Settings().value('Browser-View-Settings/instantBookmarksToolbar', type=bool):
            self._window.bookmarksToolbar().hide()

    # override
    def keyPressEvent(self, event):  # noqa C901
        '''
        @param: event QKeyEvent
        '''
        evtKey = event.key()
        evtModifiers = event.modifiers()
        if evtKey == Qt.Key_V:
            if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                self._pasteAndGo()
                event.accept()
                return
        elif evtKey == Qt.Key_Down:
            self._completer.complete(self.text())
        elif evtKey == Qt.Key_Left:
            self._completer.closePopup()
        elif evtKey == Qt.Key_Escape:
            self._webView.setFocus()
            self.showUrl(self._webView.url())
            event.accept()
        elif evtKey == Qt.Key_Alt:
            self._holdingAlt = True
        elif evtKey in (Qt.Key_Return, Qt.Key_Enter):
            if evtModifiers == Qt.ControlModifier:
                if not self.text().endswith('.com'):
                    self.setText(self.text() + '.com')
                self.requestLoadUrl()
            elif evtModifiers == Qt.AltModifier:
                self._completer.closePopup()
                if self._window:
                    req = self.loadAction(self.text()).loadRequest
                    self._window.tabWidget().addViewByReq(req)
            else:
                self._requestLoadUrl()

            self._holdingAlt = False

        elif evtKey in (
            Qt.Key_0,
            Qt.Key_1,
            Qt.Key_2,
            Qt.Key_3,
            Qt.Key_4,
            Qt.Key_5,
            Qt.Key_6,
            Qt.Key_7,
            Qt.Key_8,
            Qt.Key_9,
        ):
            if evtModifiers & Qt.AltModifier or evtModifiers & Qt.ControlModifier:
                event.ignore()
                self._holdingAlt = False
                return
        else:
            self._holdingAlt = False

        super().keyPressEvent(event)

    # override
    def dropEvent(self, event):
        '''
        @param: event QDropEvent
        '''
        if event.mimeData().hasUrls():
            dropUrl = event.mimeData().urls()[0]
            if WebView.isUrlValid(dropUrl):
                self.setText(dropUrl.toString())
                self.loadRequest(LoadRequest(dropUrl))

                event = QFocusEvent(QFocusEvent.FocusOut)
                super().focusOutEvent(event)
                return
        elif event.mimeData().hasText():
            dropText = event.mimeData().text().strip()
            dropUrl = QUrl(dropText)
            if WebView.isUrlValid(dropUrl):
                self.setText(dropUrl.toString())
                self.loadRequest(LoadRequest(dropUrl))

                event = QFocusEvent(QFocusEvent.FocusOut)
                super().focusOutEvent(event)
                return
            else:
                self.setText(dropText)
                self.setFocus()
                return

        super().dropEvent(event)

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        super().paintEvent(event)

        # Show loading progress
        if gVar.appSettings.showLoadingProgress and self._progressVisible:
            option = QStyleOptionFrame()
            self.initStyleOption(option)

            lm, tm, rm, bm = self.getTextMargins()

            contentsRect = self.style().subElementRect(QStyle.SE_LineEditContents, option, self)
            contentsRect.adjust(lm, tm, -rm, -bm)

            bg = QColor(self._progressColor)
            if not bg.isValid() or bg.alpha() == 0:
                pal = self.palette()
                bg = Colors.mid(pal.color(QPalette.Base), pal.color(QPalette.Text),
                        self._progressStyle > 0 and 4 or 8, 1)

            p = QPainter(self)
            p.setBrush(QBrush(bg))

            # We are painting over text, make sure the text stays visible
            p.setOpacity(0.5)

            outlinePen = QPen(bg.darker(110), 0.8)
            p.setPen(outlinePen)

            if self._progressStyle == self._ProgressFilled:
                bar = contentsRect.adjusted(0, 1, 0, -1)
                bar.setWidth(int(bar.width() * self._loadProgress / 100))
                roundness = bar.height() / 4.0
                p.drawRoundedRect(bar, roundness, roundness)
            elif self._progressStyle == self._ProgressBottom:
                outlinePen.setWidthF(0.3)
                outlinePen.setColor(outlinePen.color().darker(130))
                p.setPen(outlinePen)
                bar = QRect(contentsRect.x(), contentsRect.bottom() - 3,
                        contentsRect.width() * self._loadProgress / 100.0, 3)
                p.drawRoundedRect(bar, 1, 1)
            elif self._progressStyle == self._ProgressTop:
                outlinePen.setWidthF(0.3)
                outlinePen.setColor(outlinePen.color().darker(130))
                p.setPen(outlinePen)
                bar = QRect(contentsRect.x(), contentsRect.top() + 1,
                        contentsRect.width() * self._loadProgress / 100.0, 3)
                p.drawRoundedRect(bar, 1, 1)

    def _refreshTextFormat(self):
        if not self._webView:
            return

        textFormat = []  # typedef QList<QTextLayout::FormatRange>
        if self._webView.url().isEmpty():
            hostName = QUrl(self.text()).host()
        else:
            hostName = self._webView.url().host()

        if hostName:
            hostPos = self.text().find(hostName)
            if hostPos > 0:
                format_ = QTextCharFormat()
                palette = self.palette()
                color = Colors.mid(palette.color(QPalette.Base), palette.color(QPalette.Text), 1, 1)
                format_.setForeground(color)

                schemePart = QTextLayout.FormatRange()
                schemePart.start = 0
                schemePart.length = hostPos
                schemePart.format = format_

                hostPart = QTextLayout.FormatRange()
                hostPart.start = hostPos
                hostPart.length = len(hostName)

                remainingPart = QTextLayout.FormatRange()
                remainingPart.start = hostPos + len(hostName)
                remainingPart.length = len(self.text()) - remainingPart.start
                remainingPart.format = format_

                textFormat.append(schemePart)
                textFormat.append(hostPart)
                textFormat.append(remainingPart)

        self.setTextFormat(textFormat)
