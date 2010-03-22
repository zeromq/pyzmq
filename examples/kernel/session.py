import os
import uuid
import pprint

def msg_header(msg_id, username, session):
    return {
        'msg_id' : msg_id,
        'username' : username,
        'session' : session
    }


def extract_header(msg_or_header):
    """Given a message or header, return the header."""
    if not msg_or_header:
        return {}
    try:
        # See if msg_or_header is the entire message.
        h = msg_or_header['header']
    except KeyError:
        try:
            # See if msg_or_header is just the header
            h = msg_or_header['msg_id']
        except KeyError:
            raise
        else:
            h = msg_or_header
    return h


class Bunch(object):
    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return pprint.pformat(self.__dict__)


def msg2obj(msg):
    """Convert a message to a simple object with attributes."""
    obj = Bunch()
    for k, v in msg.iteritems():
        if isinstance(v, dict):
            v = msg2obj(v)
        setattr(obj, k, v)
    return obj


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
        msg['parent_header'] = {} if parent is None else extract_header(parent)
        msg['msg_type'] = msg_type
        msg['content'] = {} if content is None else content
        return msg


def test_msg2obj():
    am = dict(x=1)
    ao = msg2obj(am)
    assert ao.x == am['x']

    am['y'] = dict(z=1)
    ao = msg2obj(am)
    assert ao.y.z == am['y']['z']
    
