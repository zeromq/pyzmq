#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
# stdlib imports
import os
import sys

# local imports
sys.path.append(os.path.abspath('sphinxext'))
# import sphinx_cython
from apigen import ApiDocWriter

#*****************************************************************************
if __name__ == '__main__':
    pjoin = os.path.join
    package = 'zmq'
    outdir = pjoin('source','api','generated')
    docwriter = ApiDocWriter(package,rst_extension='.rst')
    # You have to escape the . here because . is a special char for regexps.
    # You must do make clean if you change this!
    docwriter.package_skip_patterns += [ r'\.tests$', r'\.platform$' ]

    docwriter.module_skip_patterns += [ r'\.tests' ]
    
    # Now, generate the outputs
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'gen',
                          relative_to = pjoin('source','api')
                          )
    print '%d files written' % len(docwriter.written_modules)
