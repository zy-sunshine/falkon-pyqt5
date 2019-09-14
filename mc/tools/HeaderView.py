from PyQt5.Qt import QHeaderView
from PyQt5.Qt import QByteArray
from PyQt5.Qt import Qt
from PyQt5.Qt import QAction
from PyQt5.QtWidgets import QMenu

class HeaderView(QHeaderView):
    def __init__(self, parent):
        '''
        @param: parent QAbstractItem
        '''
        super().__init__(Qt.Horizontal, parent)
        self._parent = parent  # QAbstractItemView
        self._menu = None  # QMenu

        self._resizeOnShow = False
        self._sectionSizes = []  # QList<double>
        self._restoreData = QByteArray()

        self.setSectionsMovable(True)
        self.setStretchLastSection(True)
        self.setDefaultAlignment(Qt.AlignLeft)
        self.setMinimumSectionSize(60)

    def setDefaultSelectionSizes(self, sizes):
        '''
        @param: sizes QList<double>
        '''
        self._sectionSizes = sizes

    def defaultSelectionSizes(self):
        '''
        @return: QList<double>
        '''
        return self._sectionSizes

    def restoreState(self, state):
        '''
        @param: state QByteArray
        @return: bool
        '''
        self._resizeOnShow = not super().restoreState(state)
        return not self._resizeOnShow

    # private Q_SLOTS:
    def _toggleSectionVisibility(self):
        act = self.sender()
        if isinstance(act, QAction):
            index = act.data()  # toInt()
            self.setSectionHidden(index, not self.isSectionHidden(index))

    # private:
    # override
    def showEvent(self, event):
        '''
        @param: event QShowEvent
        '''
        if self._resizeOnShow:
            for idx, size in enumerate(self._sectionSizes):
                size = self._parent.width() * size
                self.resizeSection(idx, size)

        super().showEvent(event)

    # override
    def contextMenuEvent(self, event):
        '''
        @param: event QContextMenuEvent
        '''
        if not self._menu:
            self._menu = QMenu(self)

            for idx in range(self.count()):
                act = QAction(self.model().headerData(idx, Qt.Horizontal), self._menu)
                act.setCheckable(True)
                act.setData(idx)

                act.triggered.connect(self._toggleSectionVisibility)
                self._menu.addAction(act)

        for idx, act in enumerate(self._menu.actions()):
            act.setEnabled(idx > 0)
            act.setChecked(not self.isSectionHidden(idx))

        self._menu.popup(event.globalPos())
