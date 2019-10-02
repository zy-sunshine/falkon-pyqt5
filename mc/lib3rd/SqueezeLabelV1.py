from PyQt5.QtWidgets import QLabel
from PyQt5.Qt import Qt

class SqueezeLabelV1(QLabel):
    '''
    @note: A label that will squeeze the set text to fit within the size of the
        widget. The text will be elided in the middle
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self._SqueezedTextCache = ''

    # override
    def paintEvent(self, event):
        '''
        @param: event QPaintEvent
        '''
        if self._SqueezedTextCache != self.text():
            self._SqueezedTextCache = self.text()
            # QFontMetrics
            fm = self.fontMetrics()
            if fm.width(self._SqueezedTextCache) > self.contentsRect().width():
                elided = fm.elidedText(self.text(), Qt.ElideMiddle, self.width())
                self.setText(elided)
        super().paintEvent(event)
