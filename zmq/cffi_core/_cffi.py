# coding: utf-8

from cffi import FFI

try:
    # below 3.3
    from threading import _Event as Event
except (ImportError):
    from threading import Event

class PythonFFI(FFI):

    def __init__(self, backend=None):
        FFI.__init__(self, backend=backend)
        self._pyexports = {}

    def pyexport(self, signature):
        tp = self._typeof(signature, consider_function_as_funcptr=True)
        def decorator(func):
            name = func.__name__
            if name in self._pyexports:
                raise cffi.CDefError("duplicate pyexport'ed function %r"
                                     % (name,))
            callback_var = self.getctype(tp, name)
            self.cdef("%s;" % callback_var)
            self._pyexports[name] = _PyExport(tp, func)
        return decorator

    def verify(self, source='', **kwargs):
        extras = []
        pyexports = sorted(self._pyexports.items())
        for name, export in pyexports:
            callback_var = self.getctype(export.tp, name)
            extras.append("%s;" % callback_var)
        extras.append(source)
        source = '\n'.join(extras)
        lib = FFI.verify(self, source, **kwargs)
        for name, export in pyexports:
            cb = self.callback(export.tp, export.func)
            export.cb = cb
            setattr(lib, name, cb)
        return lib


class _PyExport(object):
    def __init__(self, tp, func):
        self.tp = tp
        self.func = func

hints = []

ffi = PythonFFI()

@ffi.pyexport("void(char*, int)")
def python_free_callback(data, hint_index):
    tracker_evt = hints[hint_index][1]
    if isinstance(tracker_evt, Event):
        tracker_evt.set()

core_functions = \
'''
void* zmq_init(int);
int zmq_term(void *context);

void* zmq_socket(void *context, int type);
int zmq_close(void *socket);

int zmq_bind(void *socket, const char *endpoint);
int zmq_connect(void *socket, const char *endpoint);

int zmq_errno(void);
char * strerror(int errnum);
'''

core32_functions = \
'''
int zmq_unbind(void *socket, const char *endpoint);
int zmq_disconnect(void *socket, const char *endpoint);
int zmq_ctx_destroy(void *context);
'''

message_functions = \
'''
typedef struct {
    void *content;
    unsigned char flags;
    unsigned char vsm_size;
    unsigned char vsm_data [30];
} zmq_msg_t;

typedef ... zmq_free_fn;

int zmq_msg_init(zmq_msg_t *msg);
int zmq_msg_init_size(zmq_msg_t *msg, size_t size);
int zmq_msg_init_data(zmq_msg_t *msg,
                      void *data,
                      size_t size,
                      zmq_free_fn *ffn,
                      void *hint);

size_t zmq_msg_size(zmq_msg_t *msg);
void *zmq_msg_data(zmq_msg_t *msg);
int zmq_msg_close(zmq_msg_t *msg);

int zmq_send(void *socket, zmq_msg_t *msg, int flags);
int zmq_recv(void *socket, zmq_msg_t *msg, int flags);

int custom_zmq_msg_init(zmq_msg_t *message,
                        void *data,
                        size_t size,
                        void *hint);
'''

message32_functions = \
'''
typedef struct {unsigned char _ [32];} zmq_msg_t;
typedef ... zmq_free_fn;

int zmq_msg_init(zmq_msg_t *msg);
int zmq_msg_init_size(zmq_msg_t *msg, size_t size);
int zmq_msg_init_data(zmq_msg_t *msg,
                      void *data,
                      size_t size,
                      zmq_free_fn *ffn,
                      void *hint);

size_t zmq_msg_size(zmq_msg_t *msg);
void *zmq_msg_data(zmq_msg_t *msg);
int zmq_msg_close(zmq_msg_t *msg);

int zmq_sendmsg(void *socket, zmq_msg_t *msg, int flags);
int zmq_recvmsg(void *socket, zmq_msg_t *msg, int flags);

int custom_zmq_msg_init(zmq_msg_t *message,
                        void *data,
                        size_t size,
                        void *hint);
'''

sockopt_functions = \
'''
int zmq_getsockopt(void *socket,
                   int option_name,
                   void *option_value,
                   size_t *option_len);

int zmq_setsockopt(void *socket,
                   int option_name,
                   const void *option_value,
                   size_t option_len);
'''

polling_functions = \
'''
typedef struct
{
    void *socket;
    int fd;
    short events;
    short revents;
} zmq_pollitem_t;

int zmq_poll(zmq_pollitem_t *items, int nitems, long timeout);
'''

extra_functions = \
'''
char* strncpy(char* dest, char* orig, size_t len);
void * memcpy(void *restrict s1, const void *restrict s2, size_t n);
int get_ipc_path_max_len(void);
'''

def zmq_version_info():
    ffi_check = FFI()
    ffi_check.cdef('void zmq_version(int *major, int *minor, int *patch);')
    C_check_version = ffi_check.verify('#include <zmq.h>',
                                            libraries=['c', 'zmq'])
    major = ffi.new('int*')
    minor = ffi.new('int*')
    patch = ffi.new('int*')

    C_check_version.zmq_version(major, minor, patch)

    return (int(major[0]), int(minor[0]), int(patch[0]))

def zmq_version():
    return str(zmq_version_info()[0]) + \
           str(zmq_version_info()[1]) + \
           str(zmq_version_info()[2])

zmq_major_version = zmq_version_info()[0]

if zmq_version_info()[0] == 2:
    functions = ''.join([core_functions,
                         message_functions,
                         sockopt_functions,
                         polling_functions,
                         extra_functions])
elif zmq_version_info()[0] == 3:
    functions = ''.join([core_functions,
                         core32_functions,
                         message32_functions,
                         sockopt_functions,
                         polling_functions,
                         extra_functions])
else:
    raise Exception("Bad ZMQ Install")

ffi.cdef(functions)

C = ffi.verify('''
    #include <string.h>
    #include <zmq.h>
    #include <stdio.h>
    #include <sys/un.h>

void pyzmq_cffi_free(void *data, void* hint) {
    python_free_callback((char*)data, (int) hint);
}

int custom_zmq_msg_init(zmq_msg_t *message,
                        void *data,
                        size_t size,
                        void *hint)
{
    int rc = zmq_msg_init_data(message, data, size, pyzmq_cffi_free, hint);
    return rc;
}

int get_ipc_path_max_len(void) {
    struct sockaddr_un *dummy;
    return sizeof(dummy->sun_path) - 1;
}

''', libraries=['c', 'zmq'])

nsp = new_sizet_pointer = lambda length: ffi.new('size_t*', length)

new_uint64_pointer = lambda: (ffi.new('uint64_t*'),
                              nsp(ffi.sizeof('uint64_t')))
new_int64_pointer = lambda: (ffi.new('int64_t*'),
                             nsp(ffi.sizeof('int64_t')))
new_int_pointer = lambda: (ffi.new('int*'),
                           nsp(ffi.sizeof('int')))
new_binary_data = lambda length: (ffi.new('char[%d]' % (length)),
                                  nsp(ffi.sizeof('char') * length))

value_uint64_pointer = lambda val : (ffi.new('uint64_t*', val),
                                     ffi.sizeof('uint64_t'))
value_int64_pointer = lambda val: (ffi.new('int64_t*', val),
                                   ffi.sizeof('int64_t'))
value_int_pointer = lambda val: (ffi.new('int*', val),
                                 ffi.sizeof('int'))
value_binary_data = lambda val, length: (ffi.new('char[%d]' % (length), val),
                                         ffi.sizeof('char') * length)

def strerror(errnum):
    return ffi.string(C.strerror(errnum))

IPC_PATH_MAX_LEN = C.get_ipc_path_max_len()
