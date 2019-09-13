import peewee
from os import makedirs
from os.path import join as pathjoin, exists as pathexists, basename
from PyQt5.Qt import QSettings
from PyQt5.Qt import QMessageBox
from .DataPaths import DataPaths
from mc.common import const
from shutil import copy
from mc.common.fileutil import fileUtil
from mc.common.globalvars import gVar

class ProfileManager(object):
    def initConfigDir(self):
        '''
        @brief: make sure the config dir exists and have correct structure
        '''
        pass

    def initCurrentProfile(self, profileName):
        '''
        @brief: Set current profile name (from profiles.ini) and ensure
            dir exists with correct structure
        '''
        profilePath = DataPaths.path(DataPaths.Profiles)
        if not profileName:
            profilePath = pathjoin(profilePath, self.startingProfile())
        else:
            profilePath = pathjoin(profilePath, profileName)

        DataPaths.setCurrentProfilePath(profilePath)

        self._updateCurrentProfile()
        self._connectDatabase()

    @classmethod
    def createProfile(cls, profileName):
        '''
        @return: Return 0 on success, -1 profile already exists, -2 cannot create directory
        '''
        pass

    @classmethod
    def removeProfile(cls, profileName):
        '''
        @return: Return false on error (profile does not exists)
        '''
        pass

    @classmethod
    def currentProfile(cls):
        '''
        @brief: Name of current profile
        '''
        path = DataPaths.currentProfilePath()
        return basename(path)

    @classmethod
    def startingProfile(cls):
        '''
        @brief: Name of starting profile
        '''
        settings = QSettings(pathjoin(DataPaths.path(DataPaths.Profiles), 'profiles.ini'), QSettings.IniFormat)
        return settings.value('Profiles/startProfile', 'default')

    @classmethod
    def setStartingProfile(cls, profileName):
        pass

    @classmethod
    def availableProfiles(cls):
        '''
        @brief: Name of available profiles
        '''
        pass

    # private:
    def _updateCurrentProfile(self):
        '''
        @brief: update profile by version
        '''
        profileDir = DataPaths.currentProfilePath()
        if not pathexists(profileDir):
            makedirs(profileDir)

        versionFile = pathjoin(profileDir, 'version')
        if pathexists(versionFile):
            with open(versionFile, 'rt') as fp:
                profileVersion = fp.read()
                self._updateProfile(const.VERSION, profileVersion.strip())
        else:
            self._copyDataToProfile()
        with open(versionFile, 'wt') as fp:
            fp.write(const.VERSION)

    def _updateProfile(self, current, profile):
        pass

    def _copyDataToProfile(self):
        '''
        @brief: backup current profiles
        '''
        profileDir = DataPaths.currentProfilePath()
        browseData = pathjoin(profileDir, 'browsedata.db')

        if pathexists(browseData):
            browseDataBackup = pathjoin(profileDir, 'browsedata-backup.db')
            copy(browseData, browseDataBackup)
        sessionFile = pathjoin(profileDir, 'session.dat')
        if pathexists(sessionFile):
            versionFile = pathjoin(profileDir, 'version')
            with open(versionFile, 'rt') as fp:
                oldVersion = fp.read().strip()
            if not oldVersion:
                oldVersion = 'unknown-version'
            sessionBackup = pathjoin(profileDir, 'sessions', 'backup-%s.dat' % oldVersion)
            fileUtil.ensurefiledir(sessionBackup)
            copy(sessionFile, sessionBackup)
            text = 'Incompatible profile version has been detected. To avoid losing your profile data, they were ' + \
                'backed up in following file:<br/><br/><b>' + browseDataBackup + '<br/></b>'
            QMessageBox.warning(0, '%s: Incompatible profile version' % const.APPNAME, text)

    def _connectDatabase(self):
        db = peewee.SqliteDatabase(DataPaths.currentProfilePath() + '/browsedata.db')
        if gVar.app.isPrivate():
            # db.setConnectOptions('QSQLITE_OPEN_READONLY')
            pass

        db.connect()

        if not db.get_tables():
            from mc.common.models import tables
            for table in tables:
                table._meta.database = db
            with db.connection_context():
                db.create_tables(tables)

        gVar.sqlDatabase.setDatabase(db)
