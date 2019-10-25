from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from PyQt5.Qt import Qt
from PyQt5.Qt import QLocale
from PyQt5.Qt import QByteArray
from mc.app.Settings import Settings
from mc.common.globalvars import gVar

class AcceptLanguage(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = uic.loadUi('mc/preferences/AcceptLanguage.ui', self)

        self.setAttribute(Qt.WA_DeleteOnClose)

        self._ui.listWidget.setLayoutDirection(Qt.LeftToRight)

        settings = Settings()
        settings.beginGroup('Language')
        # QStringList
        langs = settings.value('acceptLanguage', self.defaultLanguage(), type=list)
        settings.endGroup()

        for code in langs:
            loc = QLocale(code.replace('-', '_'))
            label = ''

            if loc.language() == QLocale.C:
                label = _('Personal [%s]') % code
            else:
                label = '%s/%s [%s]' % (loc.languageToString(loc.language()),
                        loc.countryToString(loc.country()), code)
            self._ui.listWidget.addItem(label)

        self._ui.add.clicked.connect(self.addLanguage)
        self._ui.remove.clicked.connect(self.removeLanguage)
        self._ui.up.clicked.connect(self.upLanguage)
        self._ui.down.clicked.connect(self.downLanguage)

    @classmethod
    def defaultLanguage(cls):
        '''
        @return: QStringList
        '''
        longCode = QLocale.system().name().replace('_', '-')

        if len(longCode) == 5:
            ret = [longCode, longCode[:2]]
            return ret

        return [longCode]

    @classmethod
    def generateHeader(cls, langs):
        '''
        @param: langs QStringList
        @return: QByteArray
        '''
        if len(langs) == 0:
            return b''

        header = QByteArray()
        header.append(langs[0].encode())

        counter = 8
        for idx in range(1, len(langs)):
            s = ',%s;q=0.%s' % (langs[idx], counter)
            if counter != 2:
                counter -= 2
            header.append(s.encode())

        return header

    # public Q_SLOTS:
    # override
    def accept(self):
        langs = []
        for idx in range(self._ui.listWidget.count()):
            t = self._ui.listWidget.item(idx).text()
            code = t[t.index('[') + 1:]
            code = code.replace(']', '')
            langs.append(code)

        settings = Settings()
        settings.beginGroup('Language')
        settings.setValue('acceptLanguage', langs)
        settings.endGroup()

        gVar.app.networkManager().loadSettings()

        self.close()

    # private Q_SLOTS:
    def addLanguage(self):
        dialog = QDialog(self)
        ui = uic.loadUi('mc/preferences/AddAcceptLanguage.ui', dialog)
        ui.listWidget.setLayoutDirection(Qt.LeftToRight)

        allLanguages = []
        for idx in range(1 + QLocale.C, QLocale.LastLanguage + 1):
            allLanguages.extend(self._expand(QLocale.Language(idx)))

        ui.listWidget.addItems(allLanguages)

        ui.listWidget.itemDoubleClicked.connect(dialog.accept)

        if dialog.exec_() == QDialog.Rejected:
            return

        ownText = ui.ownDefinition.text()
        if ownText:
            title = _('Personal [%s]' % ownText)
            self._ui.listWidget.addItem(title)
        else:
            c = ui.listWidget.currentItem()
            if not c:
                return

            self._ui.listWidget.addItem(c.text())

    def removeLanguage(self):
        index = self._ui.listWidget.currentRow()
        self._ui.listWidget.takeItem(index)

    def upLanguage(self):
        index = self._ui.listWidget.currentRow()
        # QListWidgetItem
        currentItem = self._ui.listWidget.currentItem()

        if not currentItem or index == 0:
            return

        self._ui.listWidget.takeItem(index)
        self._ui.listWidget.insertItem(index - 1, currentItem)
        self._ui.listWidget.setCurrentItem(currentItem)

    def downLanguage(self):
        index = self._ui.listWidget.currentRow()
        # QListWidgetItem
        currentItem = self._ui.listWidget.currentItem()

        if not currentItem or index == self._ui.listWidget.count() - 1:
            return

        self._ui.listWidget.takeItem(index)
        self._ui.listWidget.insertItem(index + 1, currentItem)
        self._ui.listWidget.setCurrentItem(currentItem)

    def _expand(self, language):
        '''
        @param: QLocale::Language
        @return: QStringList
        '''
        allLanguages = []
        countries = QLocale.matchingLocales(language, QLocale.AnyScript, QLocale.AnyCountry)
        for jdx in range(0, len(countries)):
            languageString = ''
            country = countries[jdx].country()
            if len(countries) == 1:
                languageString = '%s [%s]' % (QLocale.languageToString(language),
                        QLocale(language).name().split('_')[0])
            else:
                languageString = '%s/%s [%s]' % (
                    QLocale.languageToString(language),
                    QLocale.countryToString(country),
                    ('-'.join(QLocale(language, country).name().split('_'))).lower()
                )
            if languageString not in allLanguages:
                allLanguages.append(languageString)
        return allLanguages
