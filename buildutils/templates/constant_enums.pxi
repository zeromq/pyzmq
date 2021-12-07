cdef extern from "zmq.h" nogil:
    enum: PYZMQ_DRAFT_API
    enum: ZMQ_VERSION
    enum: ZMQ_VERSION_MAJOR
    enum: ZMQ_VERSION_MINOR
    enum: ZMQ_VERSION_PATCH
    {ZMQ_ENUMS}
