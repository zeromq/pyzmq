import json
import os
import sys

import cffi

here = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(here)
zmq_dir = os.path.join(os.path.dirname(here), 'zmq')
backend_dir = os.path.join(zmq_dir, 'backend', 'cffi')

ffi = cffi.FFI()


def load_compiler_config():
    """load pyzmq compiler arguments"""
    fname = os.path.join(zmq_dir, 'utils', 'compiler.json')
    if os.path.exists(fname):
        with open(fname) as f:
            cfg = json.load(f)
    else:
        cfg = {}

    cfg.setdefault("include_dirs", [os.path.join(zmq_dir, 'utils')])
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
                p = os.path.join(repo_root, p)
            abs_paths.append(str(p))
        cfg[key] = abs_paths
    return cfg


cfg = load_compiler_config()

with open(os.path.join(backend_dir, '_cdefs.h')) as f:
    ffi.cdef(f.read())

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
    ffi.emit_c_code(sys.argv[1])
