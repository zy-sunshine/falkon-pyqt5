from PyQt5.Qt import QUrl
from PyQt5.Qt import QRect
from PyQt5.QtWebEngineWidgets import QWebEngineContextMenuData

class WebHitTestResult(object):
    def __init__(self, page, pos):
        '''
        @param: page WebPage
        @param: pos QPoint
        '''
        self._isNull = True
        self._baseUrl = QUrl()
        self._alternateText = ''
        self._boundingRect = QRect()
        self._imageUrl = QUrl()
        self._isContentEditable = False
        self._isContentSelected = False
        self._linkTitle = ''
        self._linkUrl = QUrl()
        self._mediaUrl = QUrl()
        self._mediaPaused = False
        self._mediaMuted = False
        self._pos = pos
        self._viewportPos = page.mapToViewport(self._pos)
        self._tagName = ''

        source = '''
(function() {
    var e = document.elementFromPoint(%s, %s);
    if (!e)
        return;
    function isMediaElement(e) {
        return e.tagName.toLowerCase() == 'audio' || e.tagName.toLowerCase() == 'video';
    }
    function isEditableElement(e) {
        if (e.isContentEditable)
            return true;
        if (e.tagName.toLowerCase() == 'input' || e.tagName.toLowerCase() == 'textarea')
            return e.getAttribute('readonly') != 'readonly';
        return false;
    }
    function isSelected(e) {
        var selection = window.getSelection();
        if (selection.type != 'Range')
            return false;
        return window.getSelection().containsNode(e, true);
    }
    function attributeStr(e, a) {
        return e.getAttribute(a) || '';
    }
    var res = {
        baseUrl: document.baseURI,
        alternateText: e.getAttribute('alt'),
        boundingRect: '',
        imageUrl: '',
        contentEditable: isEditableElement(e),
        contentSelected: isSelected(e),
        linkTitle: '',
        linkUrl: '',
        mediaUrl: '',
        tagName: e.tagName.toLowerCase()
    };
    var r = e.getBoundingClientRect();
    res.boundingRect = [r.top, r.left, r.width, r.height];
    if (e.tagName.toLowerCase() == 'img')
        res.imageUrl = attributeStr(e, 'src').trim();
    if (e.tagName.toLowerCase() == 'a') {
        res.linkTitle = e.text;
        res.linkUrl = attributeStr(e, 'href').trim();
    }
    while (e) {
        if (res.linkTitle == '' && e.tagName.toLowerCase() == 'a')
            res.linkTitle = e.text;
        if (res.linkUrl == '' && e.tagName.toLowerCase() == 'a')
            res.linkUrl = attributeStr(e, 'href').trim();
        if (res.mediaUrl == '' && isMediaElement(e)) {
            res.mediaUrl = e.currentSrc;
            res.mediaPaused = e.paused;
            res.mediaMuted = e.muted;
        }
        e = e.parentElement;
    }
    return res;
    })()
        '''
        js = source % (self._viewportPos.x(), self._viewportPos.y())
        # TODO: block loop?
        from mc.webengine.WebPage import WebPage
        self._init(page.url(), page.execJavaScript(js, WebPage.SafeJsWorld))

    # private:
    def _init(self, url, map_):
        '''
        @param: url QUrl
        @param: map_ QvariantMap
        '''
        if not map_:
            return

        self._isNull = False
        self._baseUrl = QUrl(map_['baseUrl'])
        self._alternateText = map_['alternateText']
        self._imageUrl = QUrl(map_['imageUrl'])
        self._isContentEditable = bool(map_['contentEditable'])
        self._isContentSelected = bool(map_['contentSelected'])
        self._linkTitle = map_['linkTitle']
        self._linkUrl = QUrl(map_['linkUrl'])
        self._mediaUrl = QUrl(map_['mediaUrl'])
        self._mediaPaused = bool(map_.get('mediaPaused', False))
        self._mediaMuted = bool(map_.get('mediaMuted', False))
        self._tagName = map_['tagName']

        rect = map_['boundingRect']  # toList() QVariantList
        if len(rect) == 4:
            self._boundingRect = QRect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))

        if not self._imageUrl.isEmpty():
            self._imageUrl = url.resolved(self._imageUrl)
        if not self._linkUrl.isEmpty():
            self._linkUrl = url.resolved(self._linkUrl)
        if not self._mediaUrl.isEmpty():
            self._mediaUrl = url.resolved(self._mediaUrl)

    def updateWithContextMenuData(self, data):
        '''
        @param: data QWebEngineContextMenuData
        '''
        if not data.isValid() or data.position() != self._pos:
            return

        self._linkTitle = data.linkText()
        self._linkUrl = data.linkUrl()
        self._isContentEditable = data.isContentEditable()
        self._isContentSelected = bool(data.selectedText())

        mediaType = data.mediaType()
        if mediaType == QWebEngineContextMenuData.MediaTypeImage:
            self._imageUrl = data.mediaUrl()
        elif mediaType in (QWebEngineContextMenuData.MediaTypeVideo,
                QWebEngineContextMenuData.MediaTypeAudio):
            self._mediaUrl = data.mediaUrl()

    def baseUrl(self):
        '''
        @return: QUrl
        '''
        return self._baseUrl()

    def alternateText(self):
        '''
        @return: QString
        '''
        return self._alternateText

    def boundingRect(self):
        '''
        @return: QRect
        '''
        return self._boundingRect

    def imageUrl(self):
        '''
        @return: QUrl
        '''
        return self._imageUrl

    def isContentEditable(self):
        return self._isContentEditable

    def isContentSelected(self):
        return self._isContentSelected

    def isNull(self):
        return self._isNull

    def linkTitle(self):
        return self._linkTitle

    def linkUrl(self):
        '''
        @return: QUrl
        '''
        return self._linkUrl

    def mediaUrl(self):
        '''
        @return: QUrl
        '''
        return self._mediaUrl

    def mediaPaused(self):
        '''
        @return: bool
        '''
        return self._mediaPaused

    def mediaMuted(self):
        '''
        @return: bool
        '''
        return self._mediaMuted

    def pos(self):
        '''
        @return: QPoint
        '''
        return self._pos

    def viewportPos(self):
        '''
        @return: QPoint
        '''
        return self._viewportPos

    def tagName(self):
        '''
        @return: QString
        '''
        return self._tagName
