# -----------------------------------------------------------------------------
#  Copyright (c) 2010 Justin Riley
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file LICENSE.BSD, distributed as part of this software.
# -----------------------------------------------------------------------------

import json
from typing import Any, Dict, List

import zmq


class MongoZMQClient:
    """
    Client that connects with MongoZMQ server to add/fetch docs
    """

    def __init__(self, connect_addr: str = 'tcp://127.0.0.1:5000'):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.DEALER)
        self._socket.connect(connect_addr)

    def _send_recv_msg(self, msg: List[bytes]) -> str:
        self._socket.send_multipart(msg)
        return self._socket.recv_multipart()[0].decode("utf8")

    def get_doc(self, keys: Dict[str, Any]) -> Dict:
        msg = [b'get', json.dumps(keys).encode("utf8")]
        json_str = self._send_recv_msg(msg)
        return json.loads(json_str)

    def add_doc(self, doc: Dict) -> str:
        msg = [b'add', json.dumps(doc).encode("utf8")]
        return self._send_recv_msg(msg)


def main() -> None:
    client = MongoZMQClient()
    for i in range(10):
        doc = {'job': str(i)}
        print("Adding doc", doc)
        print(client.add_doc(doc))
    for i in range(10):
        query = {'job': str(i)}
        print("Getting doc matching query:", query)
        print(client.get_doc(query))


if __name__ == "__main__":
    main()
