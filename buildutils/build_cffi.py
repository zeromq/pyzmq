"""Generate the CFFI backend C code"""

import sys
from pathlib import Path

import cffi

here = Path(__file__).parent.absolute()
repo_root = here.parent
zmq_dir = repo_root / 'zmq'
backend_cffi = zmq_dir / 'backend' / 'cffi'


def generate_cffi_c(dest_file: str):
    """Generate CFFI backend extension C code

    Called during build
    """

    ffi = cffi.FFI()

    with (backend_cffi / '_cdefs.h').open() as f:
        ffi.cdef(f.read())

    with (backend_cffi / '_cffi_src.c').open() as f:
        ffi.set_source(
            'zmq.backend.cffi._cffi',
            source=f.read(),
        )
    ffi.emit_c_code(dest_file)


if __name__ == "__main__":
    generate_cffi_c(sys.argv[1])
