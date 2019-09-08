from sys import stderr
from os import environ, makedirs
from os.path import join as pathjoin, exists as pathexists
from PyQt5.Qt import QTemporaryDir
from PyQt5.Qt import QCoreApplication
from PyQt5.Qt import QDir
from PyQt5.Qt import QStandardPaths
from mc.common import const
from mc.common.designutil import Singleton

class DataPaths(Singleton):
    # enum Path
    AppData = 0
    Themes = 1
    Plugins = 2
    Config = 3
    Profiles = 4
    CurrentProfile = 5
    Temp = 6
    Cache = 7
    Sessions = 8
    LastPath = 9

    def __init__(self):
        self._paths = [ [] for idx in range(self.LastPath) ]
        self._tmpdir = QTemporaryDir()
        self.init()

    @classmethod
    def setCurrentProfilePath(cls, profilePath):
        ''' Set absolute path of current profile '''
        cls.instance().initCurrentProfile(profilePath)

    @classmethod
    def setPortableVersion(cls):
        ''' Set Config path to $AppData/data '''
        d = cls.instance()
        appDir = pathjoin(const.BASE_DIR, 'data')
        d._paths[cls.AppData] = [appDir, ]
        d._paths[cls.Config] = [pathjoin(appDir, 'config')]
        d._paths[cls.Cache] = [pathjoin(appDir, 'cache')]
        d._paths[cls.Profiles] = [pathjoin(appDir, 'config', 'profiles')]

        d._paths[cls.Themes].clear()
        d._paths[cls.Themes] = [pathjoin(appDir, 'themes')]
        d._paths[cls.Plugins].clear()
        d._paths[cls.Plugins] = [pathjoin(appDir, 'plugins')]
        d.initAssertIn(appDir)

        # Make sure Temp path exists
        QDir().mkpath(d._paths[cls.Temp][0])

    @classmethod
    def path(cls, type_):
        '''
        @brief: Returns main path (Themes -> /usr/share/themes)
        @param: type_ enum Path
        '''
        assert(cls.instance()._paths[type_])
        return cls.instance()._paths[type_][0]

    @classmethod
    def allPaths(cls, type_):
        '''
        @brief: Returns all paths (Themes -> /usr/share/themes, ~/.config/demo/themes)
        @param: type_ enum Path
        '''
        assert(cls.instance()._paths[type_])
        return cls.instance()._paths[type_]

    @classmethod
    def locate(cls, type_, file_):
        '''
        @brief: Returns full path of existing file
        @param: type_ enum Path
        @param: file_ string
        '''
        dirs = cls.allPaths(type_)
        for dir_ in dirs:
            fullPath = pathjoin(dir_, file_)
            if pathexists(fullPath):
                return fullPath
        return ''

    @classmethod
    def currentProfilePath(cls):
        '''
        @brief: Convenience function for getting CurrentProfile
        @return: string
        '''
        return cls.path(cls.CurrentProfile)

    # private
    def init(self):
        from .MainApplication import MainApplication
        appDir = QCoreApplication.applicationDirPath()
        self._paths[self.AppData].extend(QStandardPaths.standardLocations(QStandardPaths.AppDataLocation))
        self._paths[self.Plugins].append(pathjoin(appDir, 'plugins'))
        for location in self._paths[self.AppData]:
            self.initAssertIn(location)
        if MainApplication.isTestModeEnabled():
            self._paths[self.Config].append(pathjoin(QDir().tempPath(), '%s-test' % const.APPNAME))
        else:
            self._paths[self.Config].append(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))

        self._paths[self.Profiles].append(pathjoin(self._paths[self.Config][0], 'profiles'))
        # We also allow to load data from Config path
        self.initAssertIn(self._paths[self.Config][0])

        # if PLUGIN_PATH is set, only load plugins from there
        pluginPath = environ.get('PLUGIN_PATH', '')
        if pluginPath:
            self._paths[self.Plugins] = [pluginPath, ]

        self._tmpdir = QTemporaryDir()
        self._paths[self.Temp].append(self._tmpdir.path())
        if not self._tmpdir.isValid():
            print('Failed to create temporary directory %s' % self._tmpdir.path(), file=stderr)

        self._paths[self.Cache].append(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))

    def initCurrentProfile(self, profilePath):
        self._paths[self.CurrentProfile].append(profilePath)

        if not self._paths[self.Cache]:
            self._paths[self.Cache].append(pathjoin(self._paths[self.CurrentProfile][0], 'cache'))

        if not self._paths[self.Sessions]:
            self._paths[self.Sessions].append(pathjoin(self._paths[self.CurrentProfile][0], 'sessions'))

        for path in (self._paths[self.Cache][0], self._paths[self.Sessions][0]):
            if not pathexists(path):
                makedirs(path)

    def initAssertIn(self, path):
        self._paths[self.Themes].append(pathjoin(path, 'themes'))
        self._paths[self.Plugins].append(pathjoin(path, 'plugins'))
