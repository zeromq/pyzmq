project('zeromq', 'c', 'cpp',
  version: '4.3.5',
  meson_version: '>= 1.3.0',
  license: ['MPL'],
  default_options: [
    'default_library=static',
  ],
)

mod = import('unstable-external_project')

# get sodium
p = mod.add_project('configure',
  configure_options: [
    '--prefix=@PREFIX@',
    '--libdir=@PREFIX@/@LIBDIR@',
    '--includedir=@PREFIX@/@INCLUDEDIR@',
    '--with-libsodium',
    '--disable-libsodium_randombytes_close',
    '--disable-Werror',
    '--disable-drafts',
    '--disable-shared',
    '--enable-static',
  ],
  depends: subproject('libsodium').get_variable('sodium_built'),
  verbose: true,
)

zmq_static = p.dependency('zmq')
meson.override_dependency('zmq_static', zmq_static)
