from PyQt5.Qt import QObject
from PyQt5.Qt import pyqtSignal, pyqtSlot
from .PluginInterface import PluginInterface
from PyQt5.Qt import QPixmap

class PluginSpec:
    def __init__(self):
        self.name = ''
        self.description = ''
        self.author = ''
        self.version = ''
        self.icon = QPixmap()
        self.hasSettings = False

        def __eq__(self, other):
            return (self.name == other.name and
                    self.description == other.description and
                    self.author == other.author and
                    self.version == other.version)

class Plugins(QObject):
    class Plugin:
        # enum Type
        Invalid = 0
        InternalPlugin = 1
        SharedLibraryPlugin = 2
        PythonPlugin = 3
        QmlPlugin = 4

        def __init__(self):
            self.type = self.Invalid
            self.pluginId = ''
            self.pluginSpec = PluginSpec()
            self.instance = None  # PluginInterface

            # InternalPlugin
            self.internalInstance = None

            # SharedLibraryPlugin
            self.libraryPath = ''
            self.pluginLoader = None  # QPluginLoader

            # Other
            self.data = None

        def isLoaded(self):
            return not not self.instance

        def __eq__(self, other):
            return (self.type == other.type and
                    self.pluginId == other.pluginId)

    def __init__(self, parent=None):
        super().__init__(parent)
        # protected:
        self._loadedPlugins = []  # QList<PluginInterface>

        # private:
        self._availablePlugins = []  # QList<Plugin>
        self._allowedPlugins = []  # QStringList

        self._pluginsLoaded = False

        self._speedDial = None  # SpeedDial
        self._internalPlugins = []  # QList<PluginInterface>
        self._pythonPlugin = None  # QLibrary

    def getAvailablePlugins(self):
        '''
        @return: QList<Plugin>
        '''
        pass

    def loadPlugin(self, plugin):
        '''
        @param: plugin Plugin
        @return: bool
        '''
        pass

    def unloadPlugin(self, plugin):
        '''
        @param: plugin Plugin
        '''
        pass

    def removePlugin(self, plugin):
        '''
        @param: plugin Plugin
        '''
        pass

    def shutdown(self):
        pass

    # SpeedDial
    def speedDial(self):
        '''
        @return: SpeedDial
        '''
        return self._speedDial

    @classmethod
    def createSpec(cls, metaData):
        '''
        @param: metaData DesktopFile
        @return: PluginSpec
        '''
        pass

    # public Q_SLOTS
    def loadSettings(self):
        pass

    def loadPlugins(self):
        pass

    # Q_SIGNALS
    pluginUnloaded = pyqtSignal(PluginInterface)  # plugin
    refreshedLoadedPlugins = pyqtSignal()

    # private:
    def _loadPythonSupport(self):
        pass

    def _loadPlugin(self, id_):
        pass

    def _loadInternalPlugin(self, name):
        pass

    def _loadSharedLibraryPlugin(self, name):
        pass

    def _loadPythonPlugin(self, name):
        pass

    def _initPlugin(self, state, plugin):
        '''
        @param: state PluginInterface::InitState
        @param: plugin Plugin
        @return: bool
        '''
        pass

    def _initInternalPlugin(self, plugin):
        '''
        @param: plugin Plugin
        '''
        pass

    def _initSharedLibraryPlugin(self, plugin):
        '''
        @param: plugin Plugin
        '''
        pass

    def _initPythonPlugin(self, plugin):
        '''
        @param: plugin Plugin
        '''
        pass

    def _registerAvailablePlugin(self, plugin):
        '''
        @param: plugin Plugin
        '''
        pass

    def _refreshLoadedPlugins(self):
        pass

    def _loadAvailablePlugins(self):
        pass
