import asyncio
import aiohttp
import sys
import quamash
import PyQt5
import PyQt5.QtWidgets
from datetime import datetime

class Window(PyQt5.QtWidgets.QWidget):

    def __init__(self):

        super().__init__()

        self.resize(200, 200)
        self.setWindowTitle("Test")

        Layout = PyQt5.QtWidgets.QVBoxLayout()

        Button = PyQt5.QtWidgets.QPushButton("Get qq.com")
        Button.clicked.connect(lambda: asyncio.Task(self.aRequest("http://qq.com/"), loop=Loop))
        Layout.addWidget(Button)

        Button = PyQt5.QtWidgets.QPushButton("Get baidu.com")
        Button.clicked.connect(self._testBaidu)
        Layout.addWidget(Button)

        self.setLayout(Layout)

        self.show()

    def _testBaidu(self):
        return asyncio.Task(self.aRequest("http://www.baidu.com/"), loop=Loop)

    async def aRequest(self, url):
        print('request started')
        tsStart = datetime.now().timestamp()
        async with aiohttp.request('GET', url, loop=Loop) as resp:
            print(resp.status)
            data = await resp.read()
            #resp.close()

        tsEnd = datetime.now().timestamp()
        print('request finished %s' % (tsEnd - tsStart))
        return data
        #await asyncio.sleep(5)

if __name__ == "__main__":

    Application = PyQt5.QtWidgets.QApplication(sys.argv)
    Loop = quamash.QEventLoop(Application)
    asyncio.set_event_loop(Loop)

    _ = Window()

    with Loop:
        Loop.run_forever()
