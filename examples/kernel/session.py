import os
import uuid

def msg_header(msg_id, username, session):
    return {
        'msg_id' : msg_id,
        'username' : username,
        'session' : session
    }


class Session(object):

    def __init__(self, username=os.environ.get('USER','username')):
        self.username = username
        self.session = str(uuid.uuid4())
        self.msg_id = 0

    def msg_header(self):
        h = msg_header(self.msg_id, self.username, self.session)
        self.msg_id += 1
        return h

    def msg(self, msg_type, content=None, parent=None):
        msg = {}
        msg['header'] = self.msg_header()
        msg['parent_header'] = {} if parent is None else parent['header']
        msg['msg_type'] = msg_type
        msg['content'] = {} if content is None else content
        return msg

