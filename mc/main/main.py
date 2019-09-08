from mc.app.MainApplication import MainApplication

from PyQt5 import QtCore
import traceback, sys
import mc.data.breeze_fallback
import mc.data.data
import mc.data.html
import mc.data.icons  # noqa

import gettext
gettext.install('app', 'locale', names=['ngettext'])

if QtCore.QT_VERSION >= 0x50501:
    def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')
sys.excepthook = excepthook

def main():
    app = MainApplication(sys.argv)
    if app.isClosing():
        return 0

    #app.setProxyStyle(ProxyStyle())
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
