cython_cli = find_program('cython')
cython_gen = generator(cython_cli,
   arguments : ['--3str', '@INPUT@', '--output-file', '@OUTPUT@'],
  output : '@BASENAME@.c')

_zmq_pyx = '_zmq.py'
# _zmq_c = cython_gen.process(_zmq_pyx)

incdir = include_directories('../../utils')

py.extension_module(
  '_zmq',
  cython_gen.process('_zmq.py'),
  dependencies: libzmq,
  include_directories: incdir,
  # TODO: link_with for bundled libzmq
  install: true,
)
