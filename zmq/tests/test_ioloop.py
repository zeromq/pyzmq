# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import time
import os
import threading

import zmq
from zmq.tests import BaseZMQTestCase
from zmq.eventloop import ioloop
from zmq.eventloop.minitornado.ioloop import _Timeout
try:
    from tornado.ioloop import PollIOLoop, IOLoop as BaseIOLoop
except ImportError:
    from zmq.eventloop.minitornado.ioloop import IOLoop as BaseIOLoop


def printer():
    os.system("say hello")
    raise Exception
    print (time.time())


class Delay(threading.Thread):
    def __init__(self, f, delay=1):
        self.f=f
        self.delay=delay
        self.aborted=False
        self.cond=threading.Condition()
        super(Delay, self).__init__()
    
    def run(self):
        self.cond.acquire()
        self.cond.wait(self.delay)
        self.cond.release()
        if not self.aborted:
            self.f()
    
    def abort(self):
        self.aborted=True
        self.cond.acquire()
        self.cond.notify()
        self.cond.release()


class TestIOLoop(BaseZMQTestCase):

    def test_simple(self):
        """simple IOLoop creation test"""
        loop = ioloop.IOLoop()
        dc = ioloop.PeriodicCallback(loop.stop, 200, loop)
        pc = ioloop.PeriodicCallback(lambda : None, 10, loop)
        pc.start()
        dc.start()
        t = Delay(loop.stop,1)
        t.start()
        loop.start()
        if t.isAlive():
            t.abort()
        else:
            self.fail("IOLoop failed to exit")
    
    def test_timeout_compare(self):
        """test timeout comparisons"""
        loop = ioloop.IOLoop()
        t = _Timeout(1, 2, loop)
        t2 = _Timeout(1, 3, loop)
        self.assertEqual(t < t2, id(t) < id(t2))
        t2 = _Timeout(2,1, loop)
        self.assertTrue(t < t2)

    def test_poller_events(self):
        """Tornado poller implementation maps events correctly"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        poller = ioloop.ZMQPoller()
        poller.register(req, ioloop.IOLoop.READ)
        poller.register(rep, ioloop.IOLoop.READ)
        events = dict(poller.poll(0))
        self.assertEqual(events.get(rep), None)
        self.assertEqual(events.get(req), None)
        
        poller.register(req, ioloop.IOLoop.WRITE)
        poller.register(rep, ioloop.IOLoop.WRITE)
        events = dict(poller.poll(1))
        self.assertEqual(events.get(req), ioloop.IOLoop.WRITE)
        self.assertEqual(events.get(rep), None)
        
        poller.register(rep, ioloop.IOLoop.READ)
        req.send(b'hi')
        events = dict(poller.poll(1))
        self.assertEqual(events.get(rep), ioloop.IOLoop.READ)
        self.assertEqual(events.get(req), None)
    
    def test_instance(self):
        """Test IOLoop.instance returns the right object"""
        loop = ioloop.IOLoop.instance()
        self.assertEqual(loop.__class__, ioloop.IOLoop)
        loop = BaseIOLoop.instance()
        self.assertEqual(loop.__class__, ioloop.IOLoop)
    
    def test_close_all(self):
        """Test close(all_fds=True)"""
        loop = ioloop.IOLoop.instance()
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        loop.add_handler(req, lambda msg: msg, ioloop.IOLoop.READ)
        loop.add_handler(rep, lambda msg: msg, ioloop.IOLoop.READ)
        self.assertEqual(req.closed, False)
        self.assertEqual(rep.closed, False)
        loop.close(all_fds=True)
        self.assertEqual(req.closed, True)
        self.assertEqual(rep.closed, True)
        

