"""A Socket subclass that adds some serialization methods."""

import zlib
import pickle

import numpy

import zmq

class SerializingSocket(zmq.Socket):
    """A class with some extra serialization methods
    
    send_zipped_pickle is just like send_pyobj, but uses
    zlib to compress the stream before sending.
    
    send_array sends numpy arrays with metadata necessary
    for reconstructing the array on the other side (dtype,shape).
    """
    
    def send_zipped_pickle(self, obj, flags=0, protocol=-1):
        """pack and compress an object with pickle and zlib."""
        pobj = pickle.dumps(obj, protocol)
        zobj = zlib.compress(pobj)
        print('zipped pickle is %i bytes' % len(zobj))
        return self.send(zobj, flags=flags)
    
    def recv_zipped_pickle(self, flags=0):
        """reconstruct a Python object sent with zipped_pickle"""
        zobj = self.recv(flags)
        pobj = zlib.decompress(zobj)
        return pickle.loads(pobj)

    def send_array(self, A, flags=0, copy=True, track=False):
        """send a numpy array with metadata"""
        md = dict(
            dtype = str(A.dtype),
            shape = A.shape,
        )
        self.send_json(md, flags|zmq.SNDMORE)
        return self.send(A, flags, copy=copy, track=track)

    def recv_array(self, flags=0, copy=True, track=False):
        """recv a numpy array"""
        md = self.recv_json(flags=flags)
        msg = self.recv(flags=flags, copy=copy, track=track)
        A = numpy.frombuffer(msg, dtype=md['dtype'])
        return A.reshape(md['shape'])

class SerializingContext(zmq.Context):
    _socket_class = SerializingSocket

def main():
    ctx = SerializingContext()
    req = ctx.socket(zmq.REQ)
    rep = ctx.socket(zmq.REP)
    
    rep.bind('inproc://a')
    req.connect('inproc://a')
    A = numpy.ones((1024,1024))
    print ("Array is %i bytes" % (A.nbytes))
    
    # send/recv with pickle+zip
    req.send_zipped_pickle(A)
    B = rep.recv_zipped_pickle()
    # now try non-copying version
    rep.send_array(A, copy=False)
    C = req.recv_array(copy=False)
    print ("Checking zipped pickle...")
    print ("Okay" if (A==B).all() else "Failed")
    print ("Checking send_array...")
    print ("Okay" if (C==B).all() else "Failed")

if __name__ == '__main__':
    main()
