# -----------------------------------------------------------------------------
#  Copyright (c) 2010 Justin Riley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file LICENSE.BSD, distributed as part of this software.
# -----------------------------------------------------------------------------

import json
from typing import Any, Dict, Optional, Union

import pymongo
from bson import json_util

import zmq


class MongoZMQ:
    """
    ZMQ server that adds/fetches documents (ie dictionaries) to a MongoDB.

    NOTE: mongod must be started before using this class
    """

    def __init__(
        self, db_name: str, table_name: str, bind_addr: str = "tcp://127.0.0.1:5000"
    ):
        """
        bind_addr: address to bind zmq socket on
        db_name: name of database to write to (created if doesn't exist)
        table_name: name of mongodb 'table' in the db to write to (created if doesn't exist)
        """
        self._bind_addr = bind_addr
        self._db_name = db_name
        self._table_name = table_name
        self._conn: pymongo.MongoClient = pymongo.MongoClient()
        self._db = self._conn[self._db_name]
        self._table = self._db[self._table_name]

    def _doc_to_json(self, doc: Any) -> str:
        return json.dumps(doc, default=json_util.default)

    def add_document(self, doc: Dict) -> Optional[str]:
        """
        Inserts a document (dictionary) into mongo database table
        """
        print(f'adding document {doc}')
        try:
            self._table.insert(doc)
        except Exception as e:
            return 'Error: %s' % e
        return None

    def get_document_by_keys(self, keys: Dict[str, Any]) -> Union[Dict, str, None]:
        """
        Attempts to return a single document from database table that matches
        each key/value in keys dictionary.
        """
        print('attempting to retrieve document using keys: %s' % keys)
        try:
            return self._table.find_one(keys)
        except Exception as e:
            return 'Error: %s' % e

    def start(self) -> None:
        context = zmq.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind(self._bind_addr)
        while True:
            msg = socket.recv_multipart()
            print("Received msg: ", msg)
            if len(msg) != 3:
                error_msg = 'invalid message received: %s' % msg
                print(error_msg)
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
                print('unknown request')
            socket.send_multipart(reply)


def main() -> None:
    MongoZMQ('ipcontroller', 'jobs').start()


if __name__ == "__main__":
    main()
