from PyQt5.Qt import QCommandLineOption, QCommandLineParser
from PyQt5.Qt import QFileInfo
from PyQt5.Qt import QCoreApplication
from mc.common import const

class CommandLineOptions(object):
    class ActionPair:
        def __init__(self):
            self.action = 0  # const.CommandLineAction
            self.text = ''

    def __init__(self):
        self._actions = []  # QVector<ActionPair>
        self._parseActions()

    def getActions(self):
        return self._actions

    # private:
    def _parseActions(self):  # noqa C901
        # Options
        authorsOption = QCommandLineOption(["a", "authors"])
        authorsOption.setDescription("Displays author information.")

        profileOption = QCommandLineOption(["p", "profile"])
        profileOption.setValueName("profileName")
        profileOption.setDescription("Starts with specified profile.")

        noExtensionsOption = QCommandLineOption(["e", "no-extensions"])
        noExtensionsOption.setDescription("Starts without extensions.")

        privateBrowsingOption = QCommandLineOption(["i", "private-browsing"])
        privateBrowsingOption.setDescription("Starts private browsing.")

        portableOption = QCommandLineOption(["o", "portable"])
        portableOption.setDescription("Starts in portable mode.")

        noRemoteOption = QCommandLineOption(["r", "no-remote"])
        noRemoteOption.setDescription("Starts new browser instance.")

        newTabOption = QCommandLineOption(["t", "new-tab"])
        newTabOption.setDescription("Opens new tab.")

        newWindowOption = QCommandLineOption(["w", "new-window"])
        newWindowOption.setDescription("Opens new window.")

        downloadManagerOption = QCommandLineOption(["d", "download-manager"])
        downloadManagerOption.setDescription("Opens download manager.")

        currentTabOption = QCommandLineOption(["c", "current-tab"])
        currentTabOption.setValueName("URL")
        currentTabOption.setDescription("Opens URL in current tab.")

        openWindowOption = QCommandLineOption(["u", "open-window"])
        openWindowOption.setValueName("URL")
        openWindowOption.setDescription("Opens URL in new window.")

        fullscreenOption = QCommandLineOption(["f", "fullscreen"])
        fullscreenOption.setDescription("Toggles fullscreen.")

        wmclassOption = QCommandLineOption(["wmclass", ])
        wmclassOption.setValueName("WM_CLASS")
        wmclassOption.setDescription("Application class (X11 only).")

        # Parser
        parser = QCommandLineParser()
        parser.setApplicationDescription("QtWebEngine based browser")
        # QCommandLineOption
        helpOption = parser.addHelpOption()
        # QCommandLineOption
        versionOption = parser.addVersionOption()
        parser.addOption(authorsOption)
        parser.addOption(profileOption)
        parser.addOption(noExtensionsOption)
        parser.addOption(privateBrowsingOption)
        parser.addOption(portableOption)
        parser.addOption(noRemoteOption)
        parser.addOption(newTabOption)
        parser.addOption(newWindowOption)
        parser.addOption(downloadManagerOption)
        parser.addOption(currentTabOption)
        parser.addOption(openWindowOption)
        parser.addOption(fullscreenOption)
        parser.addOption(wmclassOption)
        parser.addPositionalArgument("URL", "URLs to open", "[URL...]")

        # parse() and not process() so we can pass arbitrary options to Chromium
        parser.parse(QCoreApplication.arguments())

        if parser.isSet(helpOption):
            parser.showHelp()

        if parser.isSet(versionOption):
            parser.showVersion()

        if parser.isSet(authorsOption):
            print("David Rosca <nowrep@gmail.com>")

            pair = self.ActionPair()
            pair.action = const.CL_ExitAction
            self._actions.append(pair)
            return

        if parser.isSet(profileOption):
            profileName = parser.value(profileOption)
            print("Falkon: Starting with profile '%s'" % profileName)

            pair = self.ActionPair()
            pair.action = const.CL_StartWithProfile
            pair.text = profileName
            self._actions.append(pair)

        if parser.isSet(noExtensionsOption):
            pair = self.ActionPair()
            pair.action = const.CL_StartWithoutAddons
            self._actions.append(pair)

        if parser.isSet(privateBrowsingOption):
            pair = self.ActionPair()
            pair.action = const.CL_StartPrivateBrowsing
            self._actions.append(pair)

        if parser.isSet(portableOption):
            pair = self.ActionPair()
            pair.action = const.CL_StartPortable
            self._actions.append(pair)

        if parser.isSet(noRemoteOption):
            pair = self.ActionPair()
            pair.action = const.CL_StartNewInstance
            self._actions.append(pair)

        if parser.isSet(newTabOption):
            pair = self.ActionPair()
            pair.action = const.CL_NewTab
            self._actions.append(pair)

        if parser.isSet(newWindowOption):
            pair = self.ActionPair()
            pair.action = const.CL_NewWindow
            self._actions.append(pair)

        if parser.isSet(downloadManagerOption):
            pair = self.ActionPair()
            pair.action = const.CL_ShowDownloadManager
            self._actions.append(pair)

        if parser.isSet(currentTabOption):
            pair = self.ActionPair()
            pair.action = const.CL_OpenUrlInCurrentTab
            pair.text = parser.value(currentTabOption)
            self._actions.append(pair)

        if parser.isSet(openWindowOption):
            pair = self.ActionPair()
            pair.action = const.CL_OpenUrlInNewWindow
            pair.text = parser.value(openWindowOption)
            self._actions.append(pair)

        if parser.isSet(fullscreenOption):
            pair = self.ActionPair()
            pair.action = const.CL_ToggleFullScreen
            self._actions.append(pair)

        if parser.isSet(wmclassOption):
            pair = self.ActionPair()
            pair.action = const.CL_WMClass
            pair.text = parser.value(wmclassOption)
            self._actions.append(pair)

        if not parser.positionalArguments():
            return

        url = parser.positionalArguments().constLast()
        fileInfo = QFileInfo(url)

        if fileInfo.exists():
            url = fileInfo.absoluteFilePath()

        if not url.isEmpty() and not url.startsWith('-'):
            pair = self.ActionPair()
            pair.action = const.CL_OpenUrl
            pair.text = url
            self._actions.append(pair)
