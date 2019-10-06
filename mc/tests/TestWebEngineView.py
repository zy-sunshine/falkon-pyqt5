import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.Qt import QUrl

#sys.argv.append("--disable-web-security")
app = QApplication(sys.argv)

with open(sys.argv[1], 'rt') as fp:
    raw_html = fp.read()

view = QWebEngineView()
view.setHtml(raw_html)
url = QUrl.fromUserInput(sys.argv[1])
print(url)
view.load(url)
view.show()

sys.exit(app.exec_())
