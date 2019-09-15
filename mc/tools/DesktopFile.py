from PyQt5.Qt import QSettings
from PyQt5.Qt import QLocale
from PyQt5.Qt import QStandardPaths

class DesktopFile(object):
    def __init__(self, fileName=None):
        self._settings = None  # QSharedPointer<QSettings>

        if fileName is not None:
            self._settings = QSettings(fileName, QSettings.IniFormat)
            self._settings.setIniCodec('UTF-8')
            self._settings.beginGroup('Desktop Entry')

    def fileName(self):
        if self._settings:
            return self._settings.fileName()
        else:
            return ''

    def name(self):
        self.value('Name', True)

    def comment(self):
        return self.value('Comment', True)

    def type(self):
        return self.value('Type')

    def icon(self):
        return self.value('Icon')

    def value(self, key, localized=False):
        if not self._settings:
            return None
        if localized:
            locale = QLocale.system()
            localeKey = '%s[%s]' % (key, locale.name())
            if self._settings.contains(localeKey):
                return self._settings.value(localeKey)
            localeKey = '%s[%s]' % (key, locale.bcp47Name())
            if self._settings.contains(localeKey):
                return self._settings.value(localeKey)
            idx = locale.name().index('_')
            if idx > 0:
                localeKey = '%s[%s]' % (key, locale.name()[:idx])
                if self._settings.contains(localeKey):
                    return self._settings.value(localeKey)
        return self._settings.value(key)

    def tryExec(self):
        if not self._settings:
            return False

        exec_ = self._settings.value('TryExec')
        if not exec_:
            return True
        if QStandardPaths.findExecutable(exec_):
            return True
        return False
