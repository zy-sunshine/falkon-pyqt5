def debug_trace():
    from PyQt5.QtCore import pyqtRemoveInputHook
    import pdb
    import sys
    pyqtRemoveInputHook()
    # set up the debugger
    debugger = pdb.Pdb()
    debugger.reset()
    # custom next to get outside of function scope
    debugger.do_next(None) # run the next command
    users_frame = sys._getframe().f_back # frame where the user invoked `pyqt_set_trace()`
    debugger.interaction(users_frame, None)
