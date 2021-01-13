import json
import os
import sys

import cffi


here = os.path.dirname(os.path.abspath(__file__))
zmq_dir = os.path.join(os.path.dirname(here), 'zmq')
backend_dir = os.path.join(zmq_dir, 'backend', 'cffi')

# load constant names without zmq being importable
sys.path.insert(0, os.path.join(zmq_dir, "utils"))
from constant_names import all_names, no_prefix

sys.path = sys.path[1:]

ffi = cffi.FFI()


def load_compiler_config():
    """load pyzmq compiler arguments"""
    fname = os.path.join(zmq_dir, 'utils', 'compiler.json')
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
                p = os.path.join(zmq_dir, p)
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

with open(os.path.join(here, "_cffi.c")) as f:
    _cffi_c = f.read()

ffi.set_source(
    'zmq.backend.cffi._cffi',
    libraries=cfg['libraries'],
    include_dirs=cfg['include_dirs'],
    library_dirs=cfg['library_dirs'],
    runtime_library_dirs=cfg['runtime_library_dirs'],
    source=_cffi_c,
)

if __name__ == "__main__":
    ffi.compile()
