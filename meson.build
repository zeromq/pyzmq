project(
  'pyzmq', 'c',
  version: '26.0.0.dev0',
  meson_version: '>= 1.0.0',
  default_options: [
  ]
)
# subproject('zmq-static')


# libzmq = dependency('libzmq', static: false)


py = import('python').find_installation(pure: false)

cc = meson.get_compiler('c')

libzmq = dependency('libzmq', static: false, required: false)
if not libzmq.found()
  libzmq = cc.find_library('zmq', has_headers: 'zmq.h', required: false)
  if not libzmq.found()
    # This will use the fallback
    libzmq = dependency('zmq_static', required: true, static: true)
  endif
endif
# libzmq = dependency('libzmqxyz', static: false, fallback: ['libzmq', 'libzmq_dep'])

subdir('zmq')
