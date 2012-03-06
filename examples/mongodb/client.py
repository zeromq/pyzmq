#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Justin Riley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import json
import zmq

class MongoZMQClient(object):
    """
    Client that connects with MongoZMQ server to add/fetch docs 
    """

    def __init__(self, connect_addr='tcp://127.0.0.1:5000'):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.DEALER)
        self._socket.connect(connect_addr)

    def _send_recv_msg(self, msg):
        self._socket.send_multipart(msg)
        return self._socket.recv_multipart()[0]

    def get_doc(self, keys):
        msg = ['get', json.dumps(keys)]
        json_str = self._send_recv_msg(msg)
        return json.loads(json_str)

    def add_doc(self, doc):
        msg = ['add', json.dumps(doc)]
        return self._send_recv_msg(msg)

def main():
    client = MongoZMQClient()
    for i in range(10):
        doc = {'job': str(i)}
        print "Adding doc", doc
        print client.add_doc(doc)
    for i in range(10):
        query = {'job': str(i)}
        print "Getting doc matching query:", query
        print client.get_doc(query)

if __name__ == "__main__":
    main()
