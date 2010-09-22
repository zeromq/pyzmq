"""a multiplexed version of the kernel example.
Now, rather than multiple clients connecting to one kernel, it's multiple clients to multiple kernels
via a relay process.  All actions are automatically load balanced across kernels via the XREQ socket."""

import zmq
import sys
import time

def main():
    # c = zmq.Context()
    
    

    ip = '127.0.0.1'
    port_base = 5555
    connection = ('tcp://%s' % ip) + ':%i'
    queue_in  = connection % port_base
    pubsub_out = connection % (port_base+1)
    
    queue_out = connection % (port_base+10)
    pubsub_in  = connection % (port_base+11)
    
    print >>sys.__stdout__, "Relaying commands..."
    # print >>sys.__stdout__, "On:",rep_conn, pub_conn

    # session = Session(username=u'kernel')
    queue = zmq.ThreadsafeDevice(zmq.QUEUE, zmq.XREP, zmq.XREQ)
    queue.bind_in(queue_in)
    queue.bind_out(queue_out)
    
    pubsub = zmq.ThreadsafeDevice(zmq.FORWARDER, zmq.SUB, zmq.PUB)
    pubsub.bind_in(pubsub_in)
    pubsub.setsockopt_in(zmq.SUBSCRIBE, "")
    pubsub.bind_out(pubsub_out)
    
    queue.start()
    pubsub.start()
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
