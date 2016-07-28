#!/usr/bin/env python
"""
invoke script for releasing pyzmq

usage:

    invoke release 14.3.1

"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


from __future__ import print_function

import glob
import os
import pipes
import re
import shutil
import sys

from contextlib import contextmanager

from invoke import task, run as invoke_run
import requests

pjoin = os.path.join

repo = "git@github.com:zeromq/pyzmq"

_framework_py = lambda xy: "/Library/Frameworks/Python.framework/Versions/{0}/bin/python{0}".format(xy)
py_exes = {
    '2.7' : _framework_py('2.7'),
    '3.4' : _framework_py('3.4'),
    '3.5' : _framework_py('3.5'),
    'pypy': "/usr/local/bin/pypy",
    'pypy3': "/usr/local/bin/pypy3",
}
egg_pys = {'2.7'}

tmp = "/tmp"
env_root = os.path.join(tmp, 'envs')
repo_root = pjoin(tmp, 'pyzmq-release')
sdist_root = pjoin(tmp, 'pyzmq-sdist')

def _py(py):
    return py_exes[py]

def run(cmd, **kwargs):
    """wrapper around invoke.run that accepts a Popen list"""
    if isinstance(cmd, list):
        cmd = " ".join(pipes.quote(s) for s in cmd)
    kwargs.setdefault('echo', True)
    return invoke_run(cmd, **kwargs)

@contextmanager
def cd(path):
    """Context manager for temporary CWD"""
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)

@task
def clone_repo(reset=False):
    """Clone the repo"""
    if os.path.exists(repo_root) and reset:
        shutil.rmtree(repo_root)
    if os.path.exists(repo_root):
        with cd(repo_root):
            run("git pull")
    else:
        run("git clone %s %s" % (repo, repo_root))

@task
def patch_version(vs):
    """Patch zmq/sugar/version.py for the current release"""
    major, minor, patch = vs_to_tup(vs)
    version_py = pjoin(repo_root, 'zmq', 'sugar', 'version.py')
    print("patching %s with %s" % (version_py, vs))
    # read version.py, minus VERSION_ constants
    with open(version_py) as f:
        pre_lines = []
        post_lines = []
        lines = pre_lines
        for line in f:
            if line.startswith("VERSION_"):
                lines = post_lines
            else:
                lines.append(line)
    
    # write new version.py with given VERSION_ constants
    with open(version_py, 'w') as f:
        for line in pre_lines:
            f.write(line)
        f.write('VERSION_MAJOR = %s\n' % major)
        f.write('VERSION_MINOR = %s\n' % minor)
        f.write('VERSION_PATCH = %s\n' % patch)
        f.write('VERSION_EXTRA = ""\n')
        for line in post_lines:
            f.write(line)

@task
def tag(vs, push=False):
    """Make the tag (don't push)"""
    patch_version(vs)
    with cd(repo_root):
        run('git commit -a -m "release {}"'.format(vs))
        run('git tag -a -m "release {0}" v{0}'.format(vs))
        if push:
            run('git push')
            run('git push --tags')

def make_env(py_exe, *packages):
    """Make a virtualenv
    
    Assumes `which python` has the `virtualenv` package
    """
    py_exe = py_exes.get(py_exe, py_exe)
    
    if not os.path.exists(env_root):
        os.makedirs(env_root)
    
    env = os.path.join(env_root, os.path.basename(py_exe))
    py = pjoin(env, 'bin', 'python')
    # new env
    if not os.path.exists(py):
        run('virtualenv {} -p {}'.format(
            pipes.quote(env),
            pipes.quote(py_exe),
        ))
        py = pjoin(env, 'bin', 'python')
        run([py, '-V'])
        install(py, 'pip', 'setuptools')
    install(py, *packages)
    return py

def build_sdist(py, upload=False):
    """Build sdists
    
    Returns the path to the tarball
    """
    with cd(repo_root):
        cmd = [py, 'setup.py', 'sdist', '--formats=zip,gztar']
        run(cmd)
        if upload:
            run(['twine', 'upload', 'dist/*'])
    
    return glob.glob(pjoin(repo_root, 'dist', '*.tar.gz'))[0]

@task
def sdist(vs, upload=False):
    clone_repo()
    tag(vs, push=upload)
    py = make_env('3.5', 'cython', 'twine')
    tarball = build_sdist(py, upload=upload)
    return untar(tarball)

def install(py, *packages):
    packages
    run([py, '-m', 'pip', 'install', '--upgrade'] + list(packages))

def vs_to_tup(vs):
    """version string to tuple"""
    return re.findall(r'\d+', vs)

def tup_to_vs(tup):
    """tuple to version string"""
    return '.'.join(tup)

def untar(tarball):
    if os.path.exists(sdist_root):
        shutil.rmtree(sdist_root)
    os.makedirs(sdist_root)
    with cd(sdist_root):
        run(['tar', '-xzf', tarball])
    
    return glob.glob(pjoin(sdist_root, '*'))[0]

def bdist(py, wheel=True, egg=False):
    py = make_env(py, 'wheel')
    cmd = [py, 'setup.py']
    if wheel:
        cmd.append('bdist_wheel')
    if egg:
        cmd.append('bdist_egg')
    cmd.append('--zmq=bundled')
    
    run(cmd)

@task
def manylinux(vs, upload=False):
    """Build manylinux wheels with Matthew Brett's manylinux-builds"""
    manylinux = '/tmp/manylinux-builds'
    if not os.path.exists(manylinux):
        with cd('/tmp'):
            run("git clone --recursive https://github.com/minrk/manylinux-builds -b pyzmq")
    else:
        with cd(manylinux):
            run("git pull")
            run("git submodule update")
    
    base_cmd = "docker run --rm -e PYZMQ_VERSIONS='{vs}' -e PYTHON_VERSIONS='{pys}' -v $PWD:/io".format(
        vs=vs,
        pys='2.7 3.4 3.5'
    )
    with cd(manylinux):
        run(base_cmd +  " quay.io/pypa/manylinux1_x86_64 /io/build_pyzmqs.sh")
        run(base_cmd +  " quay.io/pypa/manylinux1_i686 linux32 /io/build_pyzmqs.sh")
    if upload:
        py = make_env('3.5', 'twine')
        run(['twine', 'upload', os.path.join(manylinux, 'wheelhouse', '*')])

@task
def release(vs, upload=False):
    """Release pyzmq"""
    # Ensure all our Pythons exist before we start:
    for v, path in py_exes.items():
        if not os.path.exists(path):
            raise ValueError("Need %s at %s" % (v, path))
    
    # start from scrach with clone and envs
    clone_repo(reset=True)
    if os.path.exists(env_root):
        shutil.rmtree(env_root)
    
    path = sdist(vs, upload=upload)
    
    with cd(path):
        for v in py_exes:
            bdist(v, wheel=True, egg=(v in egg_pys))
        if upload:
            py = make_env('3.5', 'twine')
            run(['twine', 'upload', 'dist/*'])
    
    manylinux(vs, upload=upload)
    if upload:
        print("When AppVeyor finished building, upload artifacts with:")
        print("  invoke appveyor_artifacts {} --upload".format(vs))


_appveyor_api = 'https://ci.appveyor.com/api'
_appveyor_project = 'minrk/pyzmq'
def _appveyor_api_request(path):
    """Make an appveyor API request"""
    r = requests.get('{}/{}'.format(_appveyor_api, path),
        headers={
            # 'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json',
        }
    )
    r.raise_for_status()
    return r.json()


@task
def appveyor_artifacts(vs, dest='win-dist', upload=False):
    """Download appveyor artifacts

    If --upload is given, upload to PyPI
    """
    if not os.path.exists(dest):
        os.makedirs(dest)

    build = _appveyor_api_request('projects/{}/branch/v{}'.format(_appveyor_project, vs))
    jobs = build['build']['jobs']
    artifact_urls = []
    for job in jobs:
        artifacts = _appveyor_api_request('buildjobs/{}/artifacts'.format(job['jobId']))
        artifact_urls.extend('{}/buildjobs/{}/artifacts/{}'.format(
            _appveyor_api, job['jobId'], artifact['fileName']
        ) for artifact in artifacts)
    for url in artifact_urls:
        print("Downloading {} to {}".format(url, dest))
        fname = url.rsplit('/', 1)[-1]
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(os.path.join(dest, fname), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    if upload:
        py = make_env('3.5', 'twine')
        run(['twine', 'upload', '{}/*'.format(dest)])
    else:
        print("You can now upload these wheels with: ")
        print("  twine upload {}/*".format(dest))

