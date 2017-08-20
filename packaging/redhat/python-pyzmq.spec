#
# spec file for package python-pyzmq
#
# Copyright (c) 2017 SUSE LINUX GmbH, Nuernberg, Germany.
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

%if 0%{?centos_version} || 0%{?rhel_version} || (0%{?suse_version} == 1315 && 0%{?sle_version} == 120200)
%define skip_python3 1
%{?!python_module:%define python_module() python-%{**}}
%else
%{?!python_module:%define python_module() python-%{**} python3-%{**}}
%endif
%if 0%{?fedora}
%define _specfile %{_sourcedir}/python-pyzmq.spec
%endif

Name:           python-pyzmq
Version:        17.0.0b1
Release:        0
Summary:        Python bindings for 0MQ
License:        LGPL-3.0+ and BSD-3-Clause
Group:          Development/Languages/Python
Url:            http://github.com/zeromq/pyzmq
Source:         https://files.pythonhosted.org/packages/source/p/pyzmq/pyzmq-%{version}.tar.gz
#Source1:        python-pyzmq-rpmlintrc
# PATCH-FIX-OPENSUSE skip_test_tracker.patch
#Patch1:         skip_test_tracker.patch
BuildRequires:  fdupes
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module devel}
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module Cython}
BuildRequires:  %{python_module cffi}
BuildRequires:  %{python_module py}
BuildRequires:  zeromq-devel
Requires:       python
%if 0%{?centos_version} == 0 && 0%{?rhel_version} == 0
Recommends:     python-cffi
Recommends:     python-gevent
Recommends:     python-numpy
Recommends:     python-pexpect
Recommends:     python-py
Recommends:     python-simplejson
Recommends:     python-tornado
Recommends:     python-paramiko
Recommends:     zeromq
%endif
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%python_subpackages

%description
PyZMQ is a lightweight and super-fast messaging library built on top of
the ZeroMQ library (http://www.zeromq.org).

%package devel
Summary:        Development files for %{name}
Group:          Development/Languages/Python
Requires:       %{name} = %{version}
Requires:       python-devel
Requires:       zeromq-devel

%description devel
Development libraries and headers needed to build software using %{name}.

%prep
%setup -q -n pyzmq-%{version}
# Fix non-executable script rpmlint warning:
find examples zmq -name "*.py" -exec sed -i "s|#\!\/usr\/bin\/env python||" {} \;

#%patch1

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
%python_exec setup.py test
%endif

%files %{python_files}
%defattr(-,root,root,-)
%doc AUTHORS.md COPYING.BSD COPYING.LESSER README.md examples
%{python_sitearch}/zmq/
%{python_sitearch}/pyzmq-*-py*.egg-info
%exclude %{python_sitearch}/zmq/utils/*.h
%exclude %{python_sitearch}/zmq/backend/cffi/_verify.c
%exclude %{python_sitearch}/zmq/backend/cffi/_cdefs.h

%files %{python_files devel}
%defattr(-,root,root,-)
%{python_sitearch}/zmq/utils/*.h
%{python_sitearch}/zmq/backend/cffi/_verify.c
%{python_sitearch}/zmq/backend/cffi/_cdefs.h

%changelog
* Sun Aug 20 2017 pyzmq developers <zeromq-dev@lists.zeromq.org>
- Initial packaging.
