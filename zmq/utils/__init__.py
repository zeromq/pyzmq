import os

if os.name == 'nt':
    from .win32 import patch_win32_ctrlc
else:
    # This shim is not required on other systems.
    class patch_win32_ctrlc(object):
        def __init__(self, action):
            self.action = action
        def __enter__(self):
            pass
        def __exit__(self, *args):
            pass
