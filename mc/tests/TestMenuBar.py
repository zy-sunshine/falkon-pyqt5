import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import Qt

class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)

        act = self.menuBar().addAction('test')
        act.setShortcut(QKeySequence('Ctrl+M'))
        def testCb():
            print('hello')
        act.triggered.connect(testCb)
        act.setShortcutContext(Qt.WidgetShortcut)
        print(self.menuBar())
        print(act.parent())
        act.setParent(self)
        print(act.parent())
        self.addAction(act)
        self.setFocus()

        def cb():
            tt = QApplication.focusWidget()
            print(tt)
        from PyQt5.Qt import QShortcut
        self.short0 = QShortcut(QKeySequence('Ctrl+N'), self)
        self.short0.activated.connect(cb)

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Simple menu')
        self.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
