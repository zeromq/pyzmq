"""Light tests to verify that the wheel works

Just import things
"""

def test_wheel():
    import zmq
    ctx = zmq.Context()
    s = ctx.socket(zmq.PUSH)
    s.close()
    ctx.term()
