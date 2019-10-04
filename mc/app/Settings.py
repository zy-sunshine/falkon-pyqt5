from PyQt5.Qt import QSettings
from PyQt5.Qt import QVariant

class Settings(object):
    s_settings = None

    def __init__(self):
        self._openedGroup = ''
        # Save currently opened group
        if self.s_settings.group():
            self._openedGroup = self.s_settings.group()
            self.s_settings.endGroup()

    def __del__(self):
        if self.s_settings.group():
            print('Settings: Deleting object with opened group!')
            self.s_settings.endGroup()
        # Restore opened group
        if self._openedGroup:
            self.s_settings.beginGroup(self._openedGroup)

    @classmethod
    def createSettings(cls, fileName):
        cls.s_settings = QSettings(fileName, QSettings.IniFormat)

    @classmethod
    def syncSettings(cls):
        if not cls.s_settings:
            return
        cls.s_settings.sync()

    @classmethod
    def globalSettings(cls):
        '''
        @return: QSettings*
        '''
        return cls.s_settings

    @classmethod
    def staticSettings(cls):
        '''
        @return: AppSettings*
        '''
        from other.AppSettings import appSettings
        return appSettings

    def childKeys(self):
        return self.s_settings.childKeys()

    def childGroups(self):
        return self.s_settings.childGroups()

    def contains(self, key):
        return self.s_settings.contains(key)

    def remove(self, key):
        self.s_settings.remove(key)

    def setValue(self, key, defaultValue=QVariant()):
        self.s_settings.setValue(key, defaultValue)

    def value(self, key, defaultValue=QVariant(), **kwargs):
        type_ = kwargs.get('type', None)
        if type_ is None:
            if type(defaultValue) != QVariant:
                # guess defaultValue type as type
                type_ = type(defaultValue)
                if type_ == bytes:
                    from PyQt5.Qt import QByteArray
                    type_ = QByteArray
                return self.s_settings.value(key, defaultValue, type_)
            else:
                return self.s_settings.value(key, defaultValue)
        else:
            return self.s_settings.value(key, defaultValue, type=type_)
        self.s_settings.value()

    def beginGroup(self, prefix):
        self.s_settings.beginGroup(prefix)

    def endGroup(self):
        self.s_settings.endGroup()

    def sync(self):
        self.s_settings.sync()
