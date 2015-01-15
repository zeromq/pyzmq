import zmq
from zmq.eventloop import ioloop, zmqstream

"""
ioloop.install() must be called prior to instantiating *any* tornado objects,
and ideally before importing anything from tornado, just to be safe.

install() sets the singleton instance of tornado.ioloop.IOLoop with zmq's
IOLoop. If this is not done properly, multiple IOLoop instances may be
created, which will have the effect of some subset of handlers never being
called, because only one loop will be running.
"""

ioloop.install()

import tornado
import tornado.web


"""
this application can be used with echostream.py, start echostream.py,
start web.py, then every time you hit http://localhost:8888/,
echostream.py will print out 'hello'
"""

def printer(msg):
    print (msg)

ctx = zmq.Context()
s = ctx.socket(zmq.REQ)
s.connect('tcp://127.0.0.1:5555')
stream = zmqstream.ZMQStream(s)
stream.on_recv(printer)

class TestHandler(tornado.web.RequestHandler):
    def get(self):
        print ("sending hello")
        stream.send("hello")
        self.write("hello")
application = tornado.web.Application([(r"/", TestHandler)])

if __name__ == "__main__":
    application.listen(8888)
    ioloop.IOLoop.instance().start()


