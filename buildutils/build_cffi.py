import json
import os
import cffi
from zmq.utils.constant_names import all_names, no_prefix

base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'zmq')
backend_dir = os.path.join(base_dir, 'backend', 'cffi')

ffi = cffi.FFI()

def load_compiler_config():
    """load pyzmq compiler arguments"""
    fname = os.path.join(base_dir, 'utils', 'compiler.json')
    if os.path.exists(fname):
        with open(fname) as f:
            cfg = json.load(f)
    else:
        cfg = {}

    cfg.setdefault("include_dirs", [])
    cfg.setdefault("library_dirs", [])
    cfg.setdefault("runtime_library_dirs", [])
    cfg.setdefault("libraries", ["zmq"])

    # cast to str, because cffi can't handle unicode paths (?!)
    cfg['libraries'] = [str(lib) for lib in cfg['libraries']]
    if 'zmq' not in cfg['libraries']:
        cfg['libraries'].append('zmq')
    for key in ("include_dirs", "library_dirs", "runtime_library_dirs"):
        # interpret paths relative to parent of zmq (like source tree)
        abs_paths = []
        for p in cfg[key]:
            if p.startswith('zmq'):
                p = os.path.join(base_dir, p)
            abs_paths.append(str(p))
        cfg[key] = abs_paths
    return cfg

cfg = load_compiler_config()

with open(os.path.join(backend_dir, '_cdefs.h')) as f:
    ffi.cdef(f.read())


def _make_defines(names):
    _names = []
    for name in names:
        define_line = "#define %s ..." % (name)
        _names.append(define_line)

    return "\n".join(_names)

c_constant_names = ['PYZMQ_DRAFT_API']
for name in all_names:
    if no_prefix(name):
        c_constant_names.append(name)
    else:
        c_constant_names.append("ZMQ_" + name)

ffi.cdef(_make_defines(c_constant_names))

ffi.set_source('zmq.backend.cffi._cffi',
            libraries=cfg['libraries'],
            include_dirs=cfg['include_dirs'],
            library_dirs=cfg['library_dirs'],
            runtime_library_dirs=cfg['runtime_library_dirs'],
               source="""
            #include <stdio.h>
            #include <sys/un.h>
            #include <string.h>

            #include <zmq.h>
            #include "zmq_compat.h"
            #include "mutex.h"

            int get_ipc_path_max_len(void) {
                struct sockaddr_un *dummy;
                return sizeof(dummy->sun_path) - 1;
            }

            typedef struct _zhint {
                void *sock;
                mutex_t *mutex;
                size_t id;
            } zhint;

            void free_python_msg(void *data, void *vhint) {
                zmq_msg_t msg;
                zhint *hint = (zhint *)vhint;
                int rc;
                fprintf(stdout, "in free_python_msg\\n");
                if (hint != NULL) {
                    zmq_msg_init_size(&msg, sizeof(size_t));
                    memcpy(zmq_msg_data(&msg), &hint->id, sizeof(size_t));
                    rc = mutex_lock(hint->mutex);
                    if (rc != 0) {
                        fprintf(stderr, "pyzmq-gc mutex lock failed rc=%d\\n", rc);
                    }
                    rc = zmq_msg_send(&msg, hint->sock, 0);
                    if (rc < 0) {
                        /*
                         * gc socket could have been closed, e.g. during process teardown.
                         * If so, ignore the failure because there's nothing to do.
                         */
                        if (zmq_errno() != ENOTSOCK) {
                            fprintf(stderr, "pyzmq-gc send failed: %s\\n", zmq_strerror(zmq_errno()));
                        }
                    }
                    rc = mutex_unlock(hint->mutex);
                    if (rc != 0) {
                        fprintf(stderr, "pyzmq-gc mutex unlock failed rc=%d\\n", rc);
                    }
                    zmq_msg_close(&msg);
                }
            }

            int zmq_wrap_msg_init_data(zmq_msg_t *msg,
                      void *data,
                      size_t size,
                      void *hint) {
                return zmq_msg_init_data(msg, data, size, free_python_msg, hint);
            }


               """)

if __name__ == "__main__":
    ffi.compile()
