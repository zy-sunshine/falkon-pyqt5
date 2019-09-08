from queue import Queue

class WheelHelper(object):
    # enum Direction
    WheelNone = 0
    WheelUp = 1
    WheelDown = 2
    WheelLeft = 3
    WheelRight = 4

    def __init__(self):
        self._wheelDelta = 0
        self._directions = Queue()  # QQueue<Direction>

    def reset(self):
        pass

    def processEvent(self, event):
        """
        @param: event QWheelEvent
        """
        pass

    def takeDirection(self):
        """
        @return: Direction
        """
        pass
