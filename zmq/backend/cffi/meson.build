cffi_c = '_cffi.c'

cffi = custom_target(
    'cffi_c',
    command: [py, meson.source_root() / 'buildutils' / 'build_cffi.py',  '@OUTPUT@'],
    output: [cffi_c],
    # depend_files: [],
)

incdir = include_directories('../../utils')

py.extension_module(
    '_cffi',
    [cffi],
    dependencies: libzmq,
    subdir: 'zmq/backend/cffi',
    include_directories: incdir,
    # TODO: link_with for bundled libzmq
    install: true,
)
