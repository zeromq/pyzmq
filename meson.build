project(
  'pyzmq', 'c',
  version: '26.0.0.dev0',
  meson_version: '>= 1.3.0',
  default_options: [
  ]
)

fs = import('fs') 
py = import('python').find_installation(pure: false)

python3 = py.full_path()

cfg = configuration_data()

foreach key : ['zmq_prefix', 'zmq_draft_api']
    env_key = key.to_upper()
    res = run_command(python3, '-c', 'import os; print(os.environ.get("@0@", ""))'.format(env_key), check: true)
    str_value = res.stdout().strip()
    if str_value == '0'
        cfg.set(key, false)
    elif str_value == '1'
        cfg.set(key, true)
    elif str_value != ''
        cfg.set(key, str_value)
    endif
endforeach
foreach key: cfg.keys()
    message('@0@: @1@'.format(key, cfg.get(key)))
endforeach
# persist configuration (not sure why, but I used to do this in setup.py)
configure_file(output: 'configure.json', configuration: cfg, output_format: 'json')

cc = meson.get_compiler('c')


# locate libzmq
zmq_prefix = cfg.get('zmq_prefix', false)
if [false, 'default', 'auto'].contains(zmq_prefix)
    # default search for libzmq (pkg-config, etc.)
    libzmq = dependency('libzmq', static: false, required: false)
    if not libzmq.found()
      # look for libzmq, zmq.h directly
      libzmq = cc.find_library('zmq', has_headers: 'zmq.h', required: false)
      if not libzmq.found()
        # fallback on bundled
        if cfg.get('no_libzmq_extension', false)
            error('bundled libzmq is disabled, but libzmq was not found')
        endif
        libzmq = [
            dependency('zmq_static', required: true, static: true),
            dependency('sodium_static', required: true, static: true),
        ]
      endif
    endif
elif zmq_prefix == 'bundled'
    # bundle requested, no search
    libzmq = [
        dependency('zmq_static', required: true, static: true),
        dependency('sodium_static', required: true, static: true),
    ]
else
    # lookup by explicit prefix
    libzmq = cc.find_library('zmq', dirs: [zmq_prefix / 'lib'], header_include_directories: include_directories(zmq_prefix / 'include'), has_headers: 'zmq.h', required: true)
endif


subdir('zmq')
install_subdir('zmq', install_dir: py.get_install_dir(), exclude_directories: ['__pycache__'], install_tag: 'runtime')
