project('zeromq', 'c', 'cpp',
  version: '4.3.5',
  meson_version: '>= 0.65.0',
  license: ['MPL'],
  default_options: [
    'default_library=static',
]
)

mod = import('unstable-external_project')

p = mod.add_project('configure',
  configure_options: [
    '--prefix=@PREFIX@',
    '--libdir=@PREFIX@/@LIBDIR@',
    '--includedir=@PREFIX@/@INCLUDEDIR@',
    '--disable-drafts',
    '--disable-shared',
    '--enable-static',
  ],
  verbose: true,
)

zmq_static = p.dependency('zmq')
meson.override_dependency('zmq_static', zmq_static)
# meson.override_dependency('zmq', zmq_static)
