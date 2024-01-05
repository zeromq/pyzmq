project('libsodium', 'c', 'cpp',
  version: '1.0.19',
  meson_version: '>= 1.0.0',
  license: ['ISC'],
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
    '--disable-shared',
    '--enable-static',
  ],
  verbose: true,
)

sodium_static = p.dependency('sodium')
# sodium_target = custom_target('sodium_target', depends: sodium_static)
meson.override_dependency('sodium_static', sodium_static)
# empty library target so we can depend on this from zeromq
sodium_built = static_library('sodium_built', 'built.c', dependencies: sodium_static.as_link_whole(), install: false)
