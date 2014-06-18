from __future__ import print_function

import os

from functools import wraps
from zmq.tests import BaseZMQTestCase
from zmq.utils.win32 import allow_interrupt


def count_calls(f):
    @wraps(f)
    def _(*args, **kwds):
        try:
            return f(*args, **kwds)
        finally:
            _.__calls__ += 1
    _.__calls__ = 0
    return _


class TestWindowsConsoleControlHandler(BaseZMQTestCase):

    def test_handler(self):
        @count_calls
        def interrupt_polling():
            print('Caught CTRL-C!')

        if os.name == 'nt':
            from ctypes import windll
            from ctypes.wintypes import BOOL, DWORD

            kernel32 = windll.LoadLibrary('kernel32')

            # <http://msdn.microsoft.com/en-us/library/ms683155.aspx>
            GenerateConsoleCtrlEvent = kernel32.GenerateConsoleCtrlEvent
            GenerateConsoleCtrlEvent.argtypes = (DWORD, DWORD)
            GenerateConsoleCtrlEvent.restype = BOOL

            try:
                # Simulate CTRL-C event while handler is active.
                with allow_interrupt(interrupt_polling):
                    result = GenerateConsoleCtrlEvent(0, 0)
                    if result == 0:
                        raise WindowsError
            except KeyboardInterrupt:
                pass
            else:
                self.fail('Expecting `KeyboardInterrupt` exception!')

            # Make sure our handler was called.
            self.assertEqual(interrupt_polling.__calls__, 1)
        else:
            # On non-Windows systems, this utility is just a no-op!
            with allow_interrupt(interrupt_polling):
                pass
            self.assertEqual(interrupt_polling.__calls__, 0)
