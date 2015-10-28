#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Justin Riley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import zmq
import pymongo
import pymongo.json_util
import json

class MongoZMQ(object):
    """
    ZMQ server that adds/fetches documents (ie dictionaries) to a MongoDB.

    NOTE: mongod must be started before using this class
    """

    def __init__(self, db_name, table_name, bind_addr="tcp://127.0.0.1:5000"):
        """
        bind_addr: address to bind zmq socket on
        db_name: name of database to write to (created if doesn't exist)
        table_name: name of mongodb 'table' in the db to write to (created if doesn't exist)
        """
        self._bind_addr = bind_addr
        self._db_name = db_name
        self._table_name = table_name
        self._conn = pymongo.Connection()
        self._db = self._conn[self._db_name]
        self._table = self._db[self._table_name]

    def _doc_to_json(self, doc):
        return json.dumps(doc,default=pymongo.json_util.default)

    def add_document(self, doc):
        """
        Inserts a document (dictionary) into mongo database table
        """
        print 'adding docment %s' % (doc)
        try:
            self._table.insert(doc)
        except Exception,e:
            return 'Error: %s' % e

    def get_document_by_keys(self, keys):
        """
        Attempts to return a single document from database table that matches
        each key/value in keys dictionary.
        """
        print 'attempting to retrieve document using keys: %s' % keys
        try:
            return self._table.find_one(keys)
        except Exception,e:
            return 'Error: %s' % e

    def start(self):
        context = zmq.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind(self._bind_addr)
        while True:
            msg = socket.recv_multipart()
            print "Received msg: ", msg
            if  len(msg) != 3:
                error_msg = 'invalid message received: %s' % msg
                print error_msg
                reply = [msg[0], error_msg]
                socket.send_multipart(reply)
                continue
            id = msg[0]
            operation = msg[1]
            contents = json.loads(msg[2])
            # always send back the id with ROUTER
            reply = [id]
            if operation == 'add':
                self.add_document(contents)
                reply.append("success")
            elif operation == 'get':
                doc = self.get_document_by_keys(contents)
                json_doc = self._doc_to_json(doc)
                reply.append(json_doc)
            else:
                print 'unknown request'
            socket.send_multipart(reply)

def main():
    MongoZMQ('ipcontroller','jobs').start()

if __name__ == "__main__":
   main()
