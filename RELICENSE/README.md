# Permission to Relicense under MPLv2 or BSD

pyzmq starting with 26.0.0 is fully licensed under the 3-clause Modified BSD License.
A small part of the core (Cython backend only) was previously licensed under LGPLv3 for historical reasons.
Permission has been granted by the contributors of the vast majority of those components to relicense under MPLv2 or BSD.
This backend has been completely replaced in pyzmq 26, and the new implementation is fully licensed under BSD-3-Clause,
so pyzmq is now under a single license.

Original text:

Most of pyzmq is licensed under [3-Clause BSD](https://opensource.org/licenses/BSD-3-Clause).
For historical reasons, the 'core' of pyzmq (the low-level Cython bindings)
was licensed under LGPLv3, like libzmq itself.

libzmq is in the process of moving away from LGPL to the [Mozilla Public License, version
2](https://www.mozilla.org/en-US/MPL/2.0/).
I'd like to take this opportunity to follow libzmq's example and also eliminate LGPL from pyzmq.
For a similarly copyleft license, MPLv2 can be used for the core.
However, I would prefer to update the core to follow the example of the rest of pyzmq,
and adopt the 3-Clause BSD license.

This directory collects grants from individuals and firms that hold
copyrights in pyzmq to permit licensing the pyzmq code under
the MPLv2 or BSD license. See
the [0MQ Licensing Page](http://zeromq.org/area:licensing) and
[libzmq relicensing effort](https://github.com/zeromq/libzmq/pull/1917)
for some background information.

Please create a separate file in this directory for each individual
or firm holding copyright in pyzmq core, named after the individual or
firm holding the copyright.

Each patch must be made with a GitHub handle that is clearly
associated with the copyright owner, to guarantee the identity of
the signatory. Please avoid changing the files created by other
individuals or firms granting a copyright license over their
copyrights (if rewording is required contact them and ask them to
submit an updated version). This makes it easier to verify that
the license grant was made by an authorized GitHub account.
