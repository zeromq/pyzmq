#!/usr/bin/env python3
"""
invoke script for releasing pyzmq

Updates version.py and publishes tag

releases are built and uploaded from CI, following the published tag

    invoke release 21.0.0 [--upload]
"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


from __future__ import print_function

import os
import pipes
import re
import shutil
import sys

from contextlib import contextmanager

from invoke import task, run as invoke_run

PYZMQ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PYZMQ_ROOT)

pjoin = os.path.join

repo = 'git@github.com:zeromq/pyzmq'
branch = os.getenv('PYZMQ_BRANCH', 'main')

tmp = "/tmp"
env_root = os.path.join(tmp, 'envs')
repo_root = pjoin(tmp, 'pyzmq-release')


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
def clone_repo(ctx, reset=False):
    """Clone the repo"""
    if os.path.exists(repo_root) and reset:
        shutil.rmtree(repo_root)
    if os.path.exists(repo_root):
        with cd(repo_root):
            run("git checkout %s" % branch)
            run("git pull")
    else:
        run("git clone -b %s %s %s" % (branch, repo, repo_root))


@task
def patch_version(ctx, vs):
    """Patch zmq/sugar/version.py for the current release"""
    major, minor, patch, extra = vs_to_tup(vs)
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
        f.write('VERSION_EXTRA = "%s"\n' % extra)
        for line in post_lines:
            f.write(line)


@task
def tag(ctx, vs, push=False):
    """Make the tag (don't push)"""
    patch_version(ctx, vs)
    with cd(repo_root):
        run('git commit -a -m "release {}"'.format(vs))
        run('git tag -a -m "release {0}" v{0}'.format(vs))
        if push:
            run('git push --tags')
            run('git push')


def vs_to_tup(vs):
    """version string to tuple"""
    return re.match(r'(\d+)\.(\d+)\.(\d+)\.?([^\.]*)$', vs).groups()


def tup_to_vs(tup):
    """tuple to version string"""
    return '.'.join(tup)


@task
def release(ctx, vs, upload=False):
    """Publish release tag of pyzmq"""
    clone_repo(ctx)
    tag(ctx, vs, push=upload)
