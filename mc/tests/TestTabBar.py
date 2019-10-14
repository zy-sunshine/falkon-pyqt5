import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, \
    QTabBar, QVBoxLayout
#from PyQt5.Qt import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QStyle

class TabBar(QTabBar):
    def __init__(self, parent):
        super().__init__(parent)

    # override
    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(100)
        return size

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 tabs - pythonspot.com'
        self.left = 0
        self.top = 0
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()

class MyTableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabBar = TabBar(self)
        #self.tabBar.setExpanding(False)
        #self.tabBar.setMinimumWidth(100)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabBar.resize(300, 200)

        # Add tabs
        icon = self.style().standardIcon(QStyle.SP_DialogOpenButton)
        print(icon, icon.isNull())
        self.tabBar.addTab(icon, 'LongLongLongTitle')
        self.tabBar.addTab('Tab2')
        #self.tabBar.addTab(self.tab1, "Tab 1")
        #self.tabBar.addTab(self.tab2, "Tab 2")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self)
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabBar)
        self.setLayout(self.layout)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
