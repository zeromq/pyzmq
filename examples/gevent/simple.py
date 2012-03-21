from gevent import spawn, spawn_later
import zmq.green as zmq

# server
print zmq.Context
ctx = zmq.Context()
sock = ctx.socket(zmq.PUSH)
sock.bind('ipc:///tmp/zmqtest')

spawn(sock.send_pyobj, ('this', 'is', 'a', 'python', 'tuple'))
spawn_later(1, sock.send_pyobj, {'hi': 1234})
spawn_later(2, sock.send_pyobj, ({'this': ['is a more complicated object', ':)']}, 42, 42, 42))
spawn_later(3, sock.send_pyobj, 'foobar')
spawn_later(4, sock.send_pyobj, 'quit')


# client
ctx = zmq.Context() # create a new context to kick the wheels
sock = ctx.socket(zmq.PULL)
sock.connect('ipc:///tmp/zmqtest')

def get_objs(sock):
    while True:
        o = sock.recv_pyobj()
        print 'received python object:', o
        if o == 'quit':
            print 'exiting.'
            break

def print_every(s, t=None):
    print s
    if t:
        spawn_later(t, print_every, s, t)

print_every('printing every half second', 0.5)
spawn(get_objs, sock).join()

