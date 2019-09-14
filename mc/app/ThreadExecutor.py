import asyncio
from PyQt5.QtWidgets import QApplication
from mc.common.designutil import Singleton

class ThreadExecutor(Singleton):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.threadExecutor = QApplication.instance().threadExecutor

    def run(self, func):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.threadExecutor, func)
