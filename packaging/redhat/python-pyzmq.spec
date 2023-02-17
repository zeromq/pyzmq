#
# spec file for package python-pyzmq
#
# Copyright (c) 2017-2019 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

# To build with draft APIs, use "--with drafts" in rpmbuild for local builds or add
#   Macros:
#   %_with_drafts 1
# at the BOTTOM of the OBS prjconf
%bcond_with drafts

# Disable tests, they are so slow that OBS thinks the build died.
%bcond_with tests

%if (0%{?centos_version} > 0 && 0%{?centos_version} < 800) || (0%{?rhel_version} > 0 && 0%{?rhel_version} < 800) || (0%{?suse_version} == 1315 && 0%{?sle_version} == 120200)
%define skip_python3 1
%{?!python_module:%define python_module() python-%{**}}
%else
%{?!python_module:%define python_module() python-%{**} python3-%{**}}
%endif
%if 0%{?fedora} || 0%{?centos_version} >= 800 || 0%{?rhel_version} >= 800
%define _specfile %{_sourcedir}/python-pyzmq.spec
%endif

%if 0%{?fedora_version} >= 31 || 0%{?centos_version} >= 800 || 0%{?rhel_version} >= 800
Name:           python-zmq
%else
Source1:        python-pyzmq-rpmlintrc
Name:           python-pyzmq
%endif
Version:        18.1.1
Release:        0
Summary:        Python bindings for 0MQ
License:        LGPL-3.0-or-later AND BSD-3-Clause
URL:            https://github.com/zeromq/pyzmq
Source0:         https://files.pythonhosted.org/packages/source/p/pyzmq/pyzmq-%{version}.tar.gz

BuildRequires:  zeromq-devel

%if 0%{?fedora_version} >= 31 || 0%{?centos_version} >= 800 || 0%{?rhel_version} >= 800
BuildRequires:  gcc
BuildRequires:  chrpath
BuildRequires:  python3-devel
BuildRequires:  python3-packaging
BuildRequires:  python3-setuptools
BuildRequires:  python3-Cython
%if %{with tests}
BuildRequires:  python3-pytest
BuildRequires:  python3-tornado
%endif

%else

BuildRequires:  %{python_module Cython}
BuildRequires:  %{python_module cffi}
BuildRequires:  %{python_module devel}
# Test requirements
%if %{with tests}
BuildRequires:  %{python_module gevent}
BuildRequires:  %{python_module nose}
BuildRequires:  %{python_module numpy}
BuildRequires:  %{python_module paramiko}
BuildRequires:  %{python_module pexpect}
BuildRequires:  %{python_module py}
BuildRequires:  %{python_module simplejson}
BuildRequires:  %{python_module tornado}
%endif
BuildRequires:  %{python_module packaging}
BuildRequires:  %{python_module setuptools}
BuildRequires:  fdupes
BuildRequires:  python-rpm-macros
BuildRequires:  -post-build-checks

Requires:       python
%if 0%{?centos_version} == 0 && 0%{?rhel_version} == 0
Recommends:     python-cffi
Recommends:     python-gevent
Recommends:     python-numpy
Recommends:     python-paramiko
Recommends:     python-pexpect
Recommends:     python-py
Recommends:     python-simplejson
Recommends:     python-tornado
Recommends:     zeromq
%endif
%endif

%if 0%{?fedora_version} >= 31 || 0%{?centos_version} >= 800 || 0%{?rhel_version} >= 800
%description
The 0MQ lightweight messaging kernel is a library which extends the
standard socket interfaces with features traditionally provided by
specialized messaging middle-ware products. 0MQ sockets provide an
abstraction of asynchronous message queues, multiple messaging
patterns, message filtering (subscriptions), seamless access to
multiple transport protocols and more.

This package contains the python bindings.


%package -n python%{python3_pkgversion}-zmq
Summary:        %{summary}
License:        LGPLv3+
%{?python_provide:%python_provide python%{python3_pkgversion}-%{modname}}
%description -n python%{python3_pkgversion}-zmq
The 0MQ lightweight messaging kernel is a library which extends the
standard socket interfaces with features traditionally provided by
specialized messaging middle-ware products. 0MQ sockets provide an
abstraction of asynchronous message queues, multiple messaging
patterns, message filtering (subscriptions), seamless access to
multiple transport protocols and more.

This package contains the python bindings.


%package -n python%{python3_pkgversion}-zmq-tests
Summary:        %{summary}, testsuite
License:        LGPLv3+
Requires:       python%{python3_pkgversion}-zmq = %{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-%{modname}-tests}
%description -n python%{python3_pkgversion}-zmq-tests
The 0MQ lightweight messaging kernel is a library which extends the
standard socket interfaces with features traditionally provided by
specialized messaging middle-ware products. 0MQ sockets provide an
abstraction of asynchronous message queues, multiple messaging
patterns, message filtering (subscriptions), seamless access to
multiple transport protocols and more.

This package contains the testsuite for the python bindings.


%prep
%setup -q -n pyzmq-%{version}

# remove bundled libraries
rm -rf bundled

# forcibly regenerate the Cython-generated .c files:
find zmq -name "*.c" -delete
%{__python3} setup.py cython

# remove shebangs
for lib in zmq/eventloop/*.py; do
    sed '/\/usr\/bin\/env/d' $lib > $lib.new &&
    touch -r $lib $lib.new &&
    mv $lib.new $lib
done

# remove executable bits
chmod -x examples/pubsub/topics_pub.py
chmod -x examples/pubsub/topics_sub.py

# delete hidden files
#find examples -name '.*' | xargs rm -v


%build
%py3_build

%install
%global RPATH /zmq/{backend/cython,devices}
%py3_install
#pathfix.py -pn -i %{__python3} %{buildroot}%{python3_sitearch}


%check
%if 0%{?run_tests}
    # Make sure we import from the install directory
    #rm zmq/__*.py
    PYTHONPATH=%{buildroot}%{python3_sitearch} \
        %{__python3} pytest
%endif


%files -n python%{python3_pkgversion}-zmq
%license COPYING.*
%doc README.md
# examples/
%{python3_sitearch}/pyzmq-*.egg-info
%{python3_sitearch}/zmq/
%exclude %{python3_sitearch}/zmq/tests

%files -n python%{python3_pkgversion}-zmq-tests
%{python3_sitearch}/zmq/tests/

%else

%python_subpackages

%description
PyZMQ is a lightweight and super-fast messaging library built on top of
the ZeroMQ library (http://www.zeromq.org).

%package devel
Summary:        Development files for %{name}
Requires:       %{name} = %{version}
Requires:       python-devel
Requires:       zeromq-devel

%description devel
Development libraries and headers needed to build software using %{name}.

%prep
%setup -q -n pyzmq-%{version}
# Fix non-executable script rpmlint warning:
find examples zmq -name "*.py" -exec sed -i "s|#\!\/usr\/bin\/env python||" {} \;

%build
export CFLAGS="%{optflags}"
%python_build

%install
%python_install
%python_expand %fdupes %{buildroot}%{$python_sitearch}

%if %{with tests}
%check
# Remove non-deterministic authentication test
# This fails to connect randomly
rm -rf zmq/tests/test_auth.py

%if %{with drafts}
%python_exec setup.py --enable-drafts build_ext --inplace
%else
%python_exec setup.py build_ext --inplace
%endif
%python_exec pytest
%endif

%files %{python_files}
%doc AUTHORS.md LICENSE.BSD LICENSE.LESSER README.md examples
%{python_sitearch}/zmq/
%{python_sitearch}/pyzmq-*-py*.egg-info
%exclude %{python_sitearch}/zmq/utils/*.h
%exclude %{python_sitearch}/zmq/backend/cffi/_cdefs.h

%files %{python_files devel}
%{python_sitearch}/zmq/utils/*.h
%{python_sitearch}/zmq/backend/cffi/_cdefs.h

%endif

%changelog
* Sun Aug 20 2017 pyzmq developers <zeromq-dev@lists.zeromq.org>
- Initial packaging.
