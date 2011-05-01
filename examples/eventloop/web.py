import zmq
from zmq.eventloop import ioloop, zmqstream
import tornado
import tornado.web

"""
kind of hacky way to replace tornado ioloop with zmqs..
this doesn't ALWAYS work depending on what
parts of tornado you are using
"""

tornado.ioloop = ioloop


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
stream = zmqstream.ZMQStream(s, tornado.ioloop.IOLoop.instance())
stream.on_recv(printer)

class TestHandler(tornado.web.RequestHandler):
    def get(self):
        print ("sending hello")
        stream.send("hello")
        self.write("hello")
application = tornado.web.Application([(r"/", TestHandler)])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()



