import requests
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

        Button = PyQt5.QtWidgets.QPushButton("Get async lambda qq.com")
        Button.clicked.connect(lambda: asyncio.Task(self.aRequest("http://qq.com/"), loop=Loop))
        Layout.addWidget(Button)

        Button = PyQt5.QtWidgets.QPushButton("Get async baidu.com")
        Button.clicked.connect(self._testBaidu)
        Layout.addWidget(Button)

        Button = PyQt5.QtWidgets.QPushButton("Get executor baidu.com")
        Button.clicked.connect(self._testBaiduExecutor)
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

    def _testBaiduExecutor(self):
        Loop.run_in_executor(executor, self._getBaiduSync)

    def _getBaiduSync(self):
        print('request started')
        tsStart = datetime.now().timestamp()
        resp = requests.get('http://www.baidu.com')
        tsEnd = datetime.now().timestamp()
        print('request finished %s' % (tsEnd - tsStart))
        print(resp.status_code)
        #import time
        #time.sleep(2)
        return resp

if __name__ == "__main__":

    app = PyQt5.QtWidgets.QApplication(sys.argv)
    Loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(Loop)
    executor = quamash.QThreadExecutor(1)

    _ = Window()

    with Loop:
        Loop.run_forever()
