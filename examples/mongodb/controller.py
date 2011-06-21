#!/usr/bin/env python

#
#    Copyright (c) 2010 Justin Riley
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
        db_name: name of database to write to (created if doesnt exist)
        table_name: name of mongodb 'table' in the db to write to (created if doesnt exist)
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
