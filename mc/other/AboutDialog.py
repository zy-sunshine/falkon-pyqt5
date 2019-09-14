from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.Qt import Qt
from PyQt5.Qt import QIcon
from PyQt5.Qt import QSize
from mc.common import const
from PyQt5.Qt import qVersion
from mc.common.globalvars import gVar

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/other/AboutDialog.ui', self)
        self._aboutHtml = ''

        self.setAttribute(Qt.WA_DeleteOnClose)

        self._ui.label.setPixmap(QIcon(':icons/other/about.svg').pixmap(QSize(256, 100) * 1.1))

        self._showAbout()

    # private Q_SLOTS:
    def _showAbout(self):
        aboutHtml = ''
        aboutHtml += "<div style='margin:0px 20px;'>"
        aboutHtml += _("<p><b>Application version %s</b><br/>") % const.VERSION
        aboutHtml += _("<b>QtWebEngine version %s</b></p>") % qVersion()
        aboutHtml += "<p>&copy; %s %s<br/>" % (const.COPYRIGHT, const.AUTHOR)
        aboutHtml += "<a href=%s>%s</a></p>" % (const.WWWADDRESS, const.WWWADDRESS)
        aboutHtml += "<p>" + gVar.app.userAgentManager().defaultUserAgent() + "</p>"
        aboutHtml += "</div>"
        self._ui.textLabel.setText(aboutHtml)
        self.setFixedHeight(self.sizeHint().height())
