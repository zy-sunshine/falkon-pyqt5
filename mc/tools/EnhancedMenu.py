from PyQt5.Qt import QMenu
from PyQt5.Qt import pyqtSignal
from PyQt5.Qt import Qt
from PyQt5.Qt import QAction
from PyQt5.QtWidgets import QApplication

class Menu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._closeOnMiddleClick = False

    def closeOnMiddleClick(self):
        '''
        @note: Default is false, menu will NOT be closed on middle click
        '''
        return self._closeOnMiddleClick

    def setCloseOnMiddleClick(self, close):
        '''
        @param: close bool
        '''
        self._closeOnMiddleClick = close

    # public Q_SIGNALS:
    menuMiddleClicked = pyqtSignal(QMenu)

    # private:
    # override
    def mouseReleaseEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        # QAction act
        qact = self.activeAction()
        # Action act
        # TODO: Action* act = qobject_cast<Action*> (qact);
        act = qact

        evtBtn = event.button()
        evtModifiers = event.modifiers()
        if qact and qact.menu():
            # TODO: Menu* m = qobject_cast<Menu*> (qact->menu());
            m = qact.menu()
            if not m:
                super().mouseReleaseEvent(event)
                return

            if evtBtn == Qt.MiddleButton or (evtBtn == Qt.LeftButton and evtModifiers == Qt.ControlModifier):
                self._closeAllMenus()
                self.menuMiddleClicked.emit(m)

        if not act:
            super().mouseReleaseEvent(event)
            return

        if (evtBtn == Qt.LeftButton or evtBtn == Qt.RightButton) and \
                evtModifiers == Qt.NoModifier:
            self._closeAllMenus()
            act.trigger()
            event.accept()
        elif evtBtn == Qt.MiddleButton or (evtBtn == Qt.LeftButton and evtModifiers == Qt.ControlModifier):
            if (evtBtn == Qt.MiddleButton and self._closeOnMiddleClick) or evtBtn != Qt.MiddleButton:
                self._closeAllMenus()
            act.emitCtrlTriggered()
            event.accept()
        elif evtBtn == Qt.LeftButton and evtModifiers == Qt.ShiftModifier:
            self._closeAllMenus()
            act.emitShiftTriggerd()
            event.accept()

    # override
    def keyPressEvent(self, event):
        '''
        @param: event QMouseEvent
        '''
        evtKey = event.key()
        evtModifiers = event.modifiers()
        if evtKey != Qt.Key_Enter and evtKey != Qt.Key_Return:
            super().keyPressEvent(event)
            return

        # QAction qact
        qact = self.activeAction()
        # TODO: Action* act = qobject_cast<Action*> (qact);
        act = qact

        if not act:
            super().keyPressEvent(event)
            return

        if evtModifiers == Qt.NoModifier or evtModifiers == Qt.KeypadModifier:
            self._closeAllMenus()
            act.trigger()
            event.accept()
        elif evtModifiers == Qt.ControlModifier:
            self._closeAllMenus()
            act.emitCtrlTriggered()
            event.accept()
        elif evtModifiers == Qt.ShiftModifier:
            self._closeAllMenus()
            act.emitShiftTriggerd()
            event.accept()

    def _closeAllMenus(self):
        menu = self

        while menu:
            menu.close()
            # TODO: menu = qobject_cast<QMenu*>(QApplication::activePopupWidget())
            menu = QApplication.activePopupWidget()

class Action(QAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # public Q_SIGNALS:
    ctrlTriggered = pyqtSignal()
    shiftTriggered = pyqtSignal()

    # public Q_SLOTS:
    def emitCtrlTriggered(self):
        self.ctrlTriggered.emit()

    def emitShiftTriggerd(self):
        self.shiftTriggered.emit()
