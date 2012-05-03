"""Config functions"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq, copied and adapted from h5py.
#  h5py source used under the New BSD license
#
#  h5py: <http://code.google.com/p/h5py/>
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import os
import pickle

try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser

pjoin = os.path.join
from msg import debug, fatal, warn

#-----------------------------------------------------------------------------
# Utility functions (adapted from h5py: http://h5py.googlecode.com)
#-----------------------------------------------------------------------------


def loadpickle(name):
    """ Load object from pickle file, or None if it can't be opened """
    name = pjoin('conf', name)
    try:
        f = open(name,'rb')
    except IOError:
        # raise
        return None
    try:
        return pickle.load(f)
    except Exception:
        # raise
        return None
    finally:
        f.close()

def savepickle(name, data):
    """ Save to pickle file, exiting if it can't be written """
    if not os.path.exists('conf'):
        os.mkdir('conf')
    name = pjoin('conf', name)
    try:
        f = open(name, 'wb')
    except IOError:
        fatal("Can't open pickle file \"%s\" for writing" % name)
    try:
        pickle.dump(data, f, 0)
    finally:
        f.close()

def v_str(v_tuple):
    """turn (2,0,1) into '2.0.1'."""
    return ".".join(str(x) for x in v_tuple)

def get_eargs():
    """ Look for options in environment vars """

    settings = {}

    zmq = os.environ.get("ZMQ_DIR", '')
    if zmq != '':
        debug("Found environ var ZMQ_DIR=%s" % zmq)
        settings['zmq'] = zmq

    return settings

def get_cfg_args():
    """ Look for options in setup.cfg """

    settings = {}
    zmq = ''
    if not os.path.exists('setup.cfg'):
        return settings
    cfg = ConfigParser()
    cfg.read('setup.cfg')
    if 'build_ext' in cfg.sections() and \
                cfg.has_option('build_ext', 'include_dirs'):
        includes = cfg.get('build_ext', 'include_dirs')
        include = includes.split(os.pathsep)[0]
        if include.endswith('include') and os.path.isdir(include):
            zmq = include[:-8]
    if zmq != '':
        debug("Found ZMQ=%s in setup.cfg" % zmq)
        settings['zmq'] = zmq

    return settings

def get_cargs():
    """ Look for global options in the command line """
    settings = loadpickle('buildconf.pickle')
    if settings is None:  settings = {}
    for arg in sys.argv[:]:
        if arg.find('--zmq=') == 0:
            zmq = arg.split('=')[-1]
            if zmq.lower() == 'default':
                settings.pop('zmq', None)
            else:
                settings['zmq'] = zmq
            sys.argv.remove(arg)
    savepickle('buildconf.pickle', settings)
    return settings

def discover_settings():
    """ Discover custom settings for ZMQ path"""
    settings = get_cfg_args()       # lowest priority
    settings.update(get_eargs())
    settings.update(get_cargs())    # highest priority
    return settings.get('zmq')
