from sys import platform
from os.path import abspath, dirname, join as pathjoin

BASE_DIR = abspath(pathjoin(dirname(__file__), '..', '..'))
APPNAME = 'demo'
VERSION = '1.0'
AUTHOR = 'autowin'

COPYRIGHT = 'autowin.org'
WWWADDRESS = 'www.autowin.org'
BUGSADDRESS = 'bugs.autowin.org'
WIKIADDRESS = 'wiki.autowin.org'

sessionVersion = 0x0004

from PyQt5 import QtCore
QT_VERSION = QtCore.QT_VERSION
QT_VERSION_STR = QtCore.QT_VERSION_STR
QT_VERSION_MAJOR = QtCore.QT_VERSION >> 16
QT_VERSION_MINOR = (QtCore.QT_VERSION >> 8) & 0x000000FF
QT_VERSION_PATCH = QtCore.QT_VERSION & 0x0000000F
# can be used like:
#   if (QT_VERSION >= QT_VERSION_CHECK(4, 4, 0))
def QT_VERSION_CHECK(major, minor, patch):
    return ((major << 16) | (minor << 8) | (patch))
QTWEBENGINEWIDGETS_VERSION = QT_VERSION

(
    BW_FirstAppWindow,
    BW_OtherRestoredWindow,
    BW_NewWindow,
    BW_MacFirstWindow,
) = BrowserWindowType = range(4)

(
    CL_NoAction,
    CL_OpenUrl,
    CL_OpenUrlInCurrentTab,
    CL_OpenUrlInNewWindow,
    CL_StartWithProfile,
    CL_StartWithoutAddons,
    CL_NewTab,
    CL_NewWindow,
    CL_ShowDownloadManager,
    CL_ToggleFullScreen,
    CL_StartPrivateBrowsing,
    CL_StartNewInstance,
    CL_StartPortable,
    CL_ExitAction,
    CL_WMClass,
) = CommandLineAction = range(15)

(
    ON_WebView,
    ON_TabBar,
    ON_TabWidget,
    ON_BrowserWindow,
) = ObjectName = range(4)

# NT stand for new tab?
NT_SelectedTab = 1
NT_NotSelectedTab = 2
NT_CleanTab = 4
NT_TabAtTheEnd = 8
NT_NewEmptyTab = 16

NT_SelectedNewEmptyTab = NT_SelectedTab | NT_TabAtTheEnd | NT_NewEmptyTab
NT_SelectedTabAtTheEnd = NT_SelectedTab | NT_TabAtTheEnd
NT_NotSelectedTabAtTheEnd = NT_NotSelectedTab | NT_TabAtTheEnd
NT_CleanSelectedTabAtTheEnd = NT_SelectedTab | NT_TabAtTheEnd | NT_CleanTab
NT_CleanSelectedTab = NT_SelectedTab | NT_CleanTab
NT_CleanNotSelectedTab = NT_NotSelectedTab | NT_CleanTab

OS_WIN = False
OS_WIN32 = False
OS_WIN64 = False
OS_MACOS = False
OS_MAC = False
OS_LINUX = False
OS_UNIX = False
import platform as modplatform

if platform.startswith('linux'): # Linux
    OS_LINUX = True
    OS_UNIX = True
elif platform.startswith('win'):  # Windows
    OS_WIN = True
    if modplatform.machine().endswith('64'):
        OS_WIN64 = True
    else:
        OS_WIN32 = True
elif platform.startswith('darwin'):  # MAC
    OS_MAC = True
    OS_MACOS = True

if OS_WIN:
    DEFAULT_THEME_NAME = 'windows'
elif OS_MACOS:
    DEFAULT_THEME_NAME = 'mac'
elif OS_UNIX:
    DEFAULT_THEME_NAME = 'linux'
else:
    DEFAULT_THEME_NAME = 'default'

DISABLE_CHECK_UPDATES = False
DEFAULT_CHECK_DEFAULTBROWSER = True

if OS_WIN:
    DEFAULT_DOWNLOAD_USE_NATIVE_DIALOG = False
else:
    DEFAULT_DOWNLOAD_USE_NATIVE_DIALOG = True

MAIN_PATH = pathjoin(BASE_DIR, 'mc', 'main', 'main.py')

APP_SCHEME = 'app'

APP_WS_X11 = False

DISABLE_DBUS = False
