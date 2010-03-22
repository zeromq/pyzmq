=====================
Message Specification
=====================

General Message Format
=====================

General message format::

    {
        
        msg_id : 10,    # start with 0
        sender_id : uuid
        parent_id : (uuid, id)    # None/0/-1? if empty
        msg_type : 'string_message_type',
        content : 'blackbox'
    }

Side effect: (PUB/SUB)
======================


# msg_type = 'stream'
content = {
    name : 'stdout',
    data : 'blob',
}

# msg_type = 'file'
content = {
    path = 'cool.jpg',
    data : 'blob'
}

# msg_type = 'pyout'
content = {
    data = 'repr(obj)',
    prompt_number = 10
}

# msg_type = 'pyerr'
content = {
    traceback : 'full traceback',
    exc_type : 'TypeError',
    exc_value :  'msg'
}

Request/Reply
=============

Execute
-------

Request:

# msg_type = 'execute_request'
content = {
    code : 'a = 10',
}

Reply:

# msg_type = 'execute_reply'
content = {
    
}

Complete
--------

# msg_type = 'complete_request'
content = {
    text : 'a.f',    # complete on this
    line : 'print a.f'    # full line
}

# msg_type = 'complete_reply'
content = {
    completions : ['a.foo', 'a.bar']
}

Control
-------

# msg_type = 'heartbeat'
content = {

}
