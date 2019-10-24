import asyncio
# https://github.com/harvimt/quamash
from quamash import QEventLoop, QThreadExecutor
from mc.app.MainApplication import MainApplication

from PyQt5 import QtCore
import traceback, sys
import mc.data.breeze_fallback
import mc.data.data
import mc.data.html
import mc.data.icons  # noqa
from PyQt5.QtCore import QCoreApplication
from PyQt5.Qt import Qt

import gettext
gettext.install('app', 'locale', names=['ngettext'])

if QtCore.QT_VERSION >= 0x50501:
    def excepthook(type_, value, traceback_):
        traceback.print_exception(type_, value, traceback_)
        QtCore.qFatal('')
sys.excepthook = excepthook

def main():
    #QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    #QCoreApplication.setAttribute(Qt.AA_UseOpenGLES)
    app = MainApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    app.threadExecutor = QThreadExecutor(10)
    if app.isClosing():
        return 0

    #app.setProxyStyle(ProxyStyle())
    #return app.exec_()

    with loop:
        # context manager calls .close() when loop completes, and releases all resources
        loop.run_forever()

if __name__ == '__main__':
    sys.exit(main())
