from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.Qt import Qt

class TestFocusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        hbox = QHBoxLayout()
        self.lineEdit = QLineEdit()
        hbox.addWidget(self.lineEdit)
        self.setLayout(hbox)
        #self.setFocusProxy(self.lineEdit)

    # override
    def focusInEvent(self, event):
        print('focusInEvent %s' % event)
        self.lineEdit.setFocus()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    widget = TestFocusWidget()
    widget.show()
    app.exec_()
