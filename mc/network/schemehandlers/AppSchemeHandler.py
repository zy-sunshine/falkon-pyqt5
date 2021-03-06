from threading import Lock
from io import BytesIO
from base64 import b64encode
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestJob
from PyQt5.Qt import QIODevice
from PyQt5.Qt import QUrlQuery, QUrl
from PyQt5.Qt import QStyle
from mc.common import const
from mc.common.globalvars import gVar
from mc.common.designutil import cached_property
from mc.tools.IconProvider import IconProvider

class AppSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent=None):
        super().__init__(parent)

    # reload
    # override
    def requestStarted(self, job):
        '''
        @param: job QWebEngineUrlRequestJob
        '''
        if self._handleRequest(job):
            return

        knownPages = ['about', 'start', 'speeddial', 'config', 'restore', 'test']

        if job.requestUrl().path() in knownPages:
            job.reply(b'text/html', AppSchemeReply(job, job))
        else:
            job.fail(QWebEngineUrlRequestJob.UrlInvalid)

    # private:
    def _handleRequest(self, job):
        '''
        @param: job QWebEngineUrlRequestJob
        '''
        reqUrl = job.requestUrl()
        query = QUrlQuery(reqUrl)
        if not query.isEmpty() and reqUrl.path() == 'restore':
            if gVar.app.restoreManager():
                if query.hasQueryItem('new-session'):
                    gVar.app.restoreManager().clearRestoreData()
                elif query.hasQueryItem('restore-session'):
                    gVar.app.restoreSession(None, gVar.app.restoreManager().restoreData())
            gVar.app.destroyRestoreManager()
            job.redirect('app:start')
            return True
        elif reqUrl.path() == 'reportbug':
            job.redirect(QUrl(const.BUGSADDRESS))
            return True
        return False

class AppSchemeReply(QIODevice):
    def __init__(self, job, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._buffer = BytesIO()  # QBuffer
        self._pageName = ''
        self._job = job  # QWebEngineUrlRequestJob
        self._mutex = Lock()  # QMutex

        self._pageName = self._job.requestUrl().path()
        self._loadPage()

    # override
    def bytesAvailable(self):
        '''
        @return: qint64
        '''
        with self._mutex:
            return len(self._buffer.getbuffer()) - self._buffer.tell()

    # override
    def readData(self, maxSize):
        '''
        @return: char* data, qint64 maxSize
        '''
        with self._mutex:
            return self._buffer.read(maxSize)

    # override
    def writeData(self, data, len_):
        '''
        @param: data const char*
        @param: len_ qint64
        '''
        return 0

    # private Q_SLOTS:
    def _loadPage(self):
        if self._loaded: return

        contents = ''

        tpl = '<html><head></head><title>%(title)s</title><body><p>%(content)s</p></body></html>'
        if self._pageName == 'about':
            contents = tpl % {'title': 'about', 'content': 'About Page'}
        elif self._pageName == 'start':
            contents = self._startPage
        elif self._pageName == 'speeddial':
            #contents = tpl % {'title': 'speeddial', 'content': 'Speeddial Page'}
            contents = self._speeddialPage()
        elif self._pageName == 'config':
            contents = tpl % {'title': 'config', 'content': 'Config Page'}
        elif self._pageName == 'restore':
            contents = self._restorePage
        elif self._pageName == 'test':
            contents = tpl % {'title': 'test', 'content': '''Test Page<br/>
                <a href="#" onclick="javascript: alert('test')">alert</a><br/>
                <a href="#" onclick="javascript: confirm('confirm test')">confirm</a><br/>
                <a href="#" onclick="javascript: prompt('prompt test', 'prompt content')">prompt</a><br/>
                <input type="file" name="myFile" accept="image/x-png" /><br/>
                <a href="mailto:test@test.com"/>mailto</a><br/>
                <a href="#" href="appxx:testxx"/>appxx protocol</a><br/>
                <a href="#" onclick="javascript: document.documentElement.webkitRequestFullscreen()"/>
                    enter fullscreen</a><br/>
                <a href="#testFragment">test fragment</a><br/>
                <a href="#" onclick="javascript: document.webkitExitFullscreen()"/>
                    exit fullscreen</a><br/>

                <button id = "find-me">Show my location</button><br/>
                <p id = "status"></p>
                <a id = "map-link" target="_blank"></a>

                <div id="div-fullscreen">div fullscreen</div>

<script>
  function geoFindMe() {

    const status = document.querySelector('#status');
    const mapLink = document.querySelector('#map-link');

    mapLink.href = '';
    mapLink.textContent = '';

    function success(position) {
      const latitude  = position.coords.latitude;
      const longitude = position.coords.longitude;

      status.textContent = '';
      mapLink.href = `https://www.openstreetmap.org/#map=18/${latitude}/${longitude}`;
      mapLink.textContent = `Latitude: ${latitude} °, Longitude: ${longitude} °`;
    }

    function error() {
      status.textContent = 'Unable to retrieve your location';
    }

    if (!navigator.geolocation) {
      status.textContent = 'Geolocation is not supported by your browser';
    } else {
      status.textContent = 'Locating…';
      navigator.geolocation.getCurrentPosition(success, error);
    }

  }
  document.querySelector('#find-me').addEventListener('click', geoFindMe);

  function openFullscreen(element) {
    if (element.requestFullscreen) {
      element.requestFullscreen();
    } else if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen();
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullScreen();
    }
  }
  document.getElementById("div-fullscreen").addEventListener('click', function() {
    openFullscreen(this);
  }, false);
</script>
            '''}

        with self._mutex:
            self._buffer = BytesIO(contents.encode('utf8'))
        self.readyRead.emit()
        self._loaded = True

    # private:
    def _aboutPage(self):
        pass

    @cached_property
    def _startPage(self):
        sPage = ''

        sPage += gVar.appTools.readAllFileContents(":html/start.html")
        sPage = sPage.replace("%ABOUT-IMG%", "qrc:icons/other/startpage.svg")

        sPage = sPage.replace("%TITLE%", _("Start Page"))
        sPage = sPage.replace("%BUTTON-LABEL%", _("Search on Web"))
        sPage = sPage.replace("%SEARCH-BY%", _("Search results provided by DuckDuckGo"))
        sPage = sPage.replace("%WWW%", const.WIKIADDRESS)
        sPage = sPage.replace("%ABOUT-APP%", _("About App"))
        sPage = sPage.replace("%PRIVATE-BROWSING%",
            gVar.app.isPrivate() and _("<h1>Private Browsing</h1>") or '')
        sPage = sPage = gVar.appTools.applyDirectionToPage(sPage)

        return sPage

    @cached_property
    def _speeddialPageBaseContent(self):
        dPage = (
            gVar.appTools.readAllFileContents(":html/speeddial.html")
            .replace("%IMG_PLUS%", "qrc:html/plus.svg")
            .replace("%IMG_CLOSE%", "qrc:html/close.svg")
            .replace("%IMG_EDIT%", "qrc:html/edit.svg")
            .replace("%IMG_RELOAD%", "qrc:html/reload.svg")
            .replace("%LOADING-IMG%", "qrc:html/loading.gif")
            .replace("%IMG_SETTINGS%", "qrc:html/configure.svg")

            .replace("%SITE-TITLE%", _("Speed Dial"))
            .replace("%ADD-TITLE%", _("Add New Page"))
            .replace("%TITLE-EDIT%", _("Edit"))
            .replace("%TITLE-REMOVE%", _("Remove"))
            .replace("%TITLE-RELOAD%", _("Reload"))
            .replace("%TITLE-WARN%", _("Are you sure you want to remove this speed dial?"))
            .replace("%TITLE-WARN-REL%", _("Are you sure you want to reload all speed dials?"))
            .replace("%TITLE-FETCHTITLE%", _("Load title from page"))
            .replace("%JAVASCRIPT-DISABLED%", _("SpeedDial requires enabled JavaScript."))
            .replace("%URL%", _("Url"))
            .replace("%TITLE%", _("Title"))
            .replace("%APPLY%", _("Apply"))
            .replace("%CANCEL%", _("Cancel"))
            .replace("%NEW-PAGE%", _("New Page"))
            .replace("%SETTINGS-TITLE%", _("Speed Dial settings"))
            .replace("%TXT_PLACEMENT%", _("Placement: "))
            .replace("%TXT_AUTO%", _("Auto"))
            .replace("%TXT_COVER%", _("Cover"))
            .replace("%TXT_FIT%", _("Fit"))
            .replace("%TXT_FWIDTH%", _("Fit Width"))
            .replace("%TXT_FHEIGHT%", _("Fit Height"))
            .replace("%TXT_NOTE%", _("Use custom wallpaper"))
            .replace("%TXT_SELECTIMAGE%", _("Click to select image"))
            .replace("%TXT_NRROWS%", _("Maximum pages in a row:"))
            .replace("%TXT_SDSIZE%", _("Change size of pages:"))
            .replace("%TXT_CNTRDLS%", _("Center speed dials"))
        )
        dPage = gVar.appTools.applyDirectionToPage(dPage)
        return dPage

    def _speeddialPage(self):
        dPage = self._speeddialPageBaseContent

        # SpeedDial
        dial = gVar.app.plugins().speedDial()

        scriptB64 = b64encode(dial.initialScript().encode()).decode()
        page = (
            dPage.replace("%INITIAL-SCRIPT%", scriptB64)
            .replace("%IMG_BACKGROUND%", dial.backgroundImage())
            .replace("%URL_BACKGROUND%", dial.backgroundImageUrl())
            .replace("%B_SIZE%", dial.backgroundImageSize())
            .replace("%ROW-PAGES%", str(dial.pagesInRow()))
            .replace("%SD-SIZE%", str(dial.sdSize()))
            .replace("%SD-CENTER%", dial.sdCenter() and "true" or "false")
        )

        return page

    @cached_property
    def _restorePage(self):
        rPage = ''
        rPage += gVar.appTools.readAllFileContents(":html/restore.html")
        rPage = rPage.replace("%IMAGE%", gVar.appTools.pixmapToDataUrl(
            IconProvider.standardIcon(QStyle.SP_MessageBoxWarning).pixmap(45)).toString())
        rPage = rPage.replace("%TITLE%", _("Restore Session"))
        rPage = rPage.replace("%OOPS%", _("Oops, Falkon crashed."))
        rPage = rPage.replace("%APOLOGIZE%",
                _("We apologize for this. Would you like to restore the last saved state?"))
        rPage = rPage.replace("%TRY-REMOVING%",
                _("Try removing one or more tabs that you think cause troubles"))
        rPage = rPage.replace("%START-NEW%", _("Or you can start completely new session"))
        rPage = rPage.replace("%WINDOW%", _("Window"))
        rPage = rPage.replace("%WINDOWS-AND-TABS%", _("Windows and Tabs"))
        rPage = rPage.replace("%BUTTON-START-NEW%", _("Start New Session"))
        rPage = rPage.replace("%BUTTON-RESTORE%", _("Restore"))
        rPage = rPage.replace("%JAVASCRIPT-DISABLED%", _("Requires enabled JavaScript."))
        rPage = gVar.appTools.applyDirectionToPage(rPage)

        return rPage

    def _configPage(self):
        pass
