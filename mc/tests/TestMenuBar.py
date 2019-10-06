import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QKeySequence
from PyQt5.Qt import Qt
from PyQt5.Qt import QHBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenuBar

class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        #self._layout = QHBoxLayout(self)
        self._widget = QWidget(self)
        #self._layout.addWidget(self._widget)
        self._menuBar = QMenuBar(self._widget)

        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        self.statusBar()

        #menubar = self.menuBar()
        menubar = self._menuBar
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)

        act = self._menuBar.addAction('test')
        act.setShortcut(QKeySequence('Ctrl+M'))

        def testCb():
            print('hello')
        act.triggered.connect(testCb)
        act.setShortcutContext(Qt.WidgetShortcut)
        print('_menuBar parent', self._menuBar.parent())
        print('act parent', act.parent())
        print('_widget parent', self._widget.parent())
        #act.setParent(self)
        #print(act.parent())
        self.addAction(act)
        # This is important for Qt.WidgetShortcut
        # the Example is focused, and it's menu's act can trigger
        # Qt.WidgetShortcut context action
        #self.setFocus()
        #act.parent().setFocus()
        print('focusWidget', QApplication.focusWidget())

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
