project(
  'pyzmq', 'c', 'cython',
  version: '26.0.0.dev0',
  meson_version: '>= 1.0.0',
  default_options: [
  ]
)

libzmq = dependency('libzmq', static: false)

py = import('python').find_installation(pure: false)

cc = meson.get_compiler('c')
cython = meson.get_compiler('cython')

libzmq = dependency('libzmq', static: false)
# cython = find_program('cython')
# cython_gen_cpp = generator(cython_cli,
#   arguments : ['@INPUT@', '@OUTPUT@', '--cplus'],
#  output : '@BASENAME@.cpp')

libzmq_pyx = 'zmq/backend/cython/_zmq.py'

py.extension_module(
  'zmq.backend.cython._zmq',
  libzmq_pyx,
  dependencies: libzmq,
  # TODO: link_with for bundled libzmq
  install: true,
  compiler: cython,
)
