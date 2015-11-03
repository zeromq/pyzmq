"""Test asyncio support"""

try:
    from ._test_asyncio import TestAsyncIOSocket
except SyntaxError:
    pass