FROM ubuntu:22.04
RUN apt-get -y update \
 && apt-get -y install curl unzip cmake ninja-build openssl xz-utils build-essential libz-dev libssl-dev

ENV BUILD_PREFIX=/opt/build
ENV PATH=${BUILD_PREFIX}/bin:$PATH

ARG PYTHON_VERSION=3.11.8
WORKDIR /src
RUN curl -L -o python.tar.xz https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz \
 && tar -xf python.tar.xz \
 && rm python.tar.xz \
 && mv Python-* cpython

# build our 'build' python
WORKDIR /src/cpython
RUN ./configure --prefix=${BUILD_PREFIX}
RUN make -j4
RUN make install

# sanity check
RUN python3 -c 'import ssl' \
 && python3 -m ensurepip \
 && python3 -m pip install --upgrade pip

# get our cross-compile toolchain
# I'm on aarch64, so use x86_64 as host
ENV BUILD="aarch64-linux-gnu"
ENV HOST="x86_64-linux-gnu"
RUN HOST_PKG=$(echo $HOST | sed s@_@-@g) \
 && apt-get -y install binutils-$HOST_PKG gcc-$HOST_PKG g++-$HOST_PKG
ENV CC=$HOST-gcc \
    CXX=$HOST-g++

# build our 'host' python
WORKDIR /src/cpython
RUN make clean
ENV HOST_PREFIX=/opt/host
RUN ./configure \
    --prefix=${HOST_PREFIX} \
    --host=$HOST \
    --build=$BUILD \
    --with-build-python=$BUILD_PREFIX/bin/python3 \
    --without-ensurepip \
    ac_cv_buggy_getaddrinfo=no \
    ac_cv_file__dev_ptmx=yes \
    ac_cv_file__dev_ptc=no
RUN make -j4
RUN make install

WORKDIR /src

# # (optional) cross-compile libsodium, libzmq
# WORKDIR /src
# ENV LIBSODIUM_VERSION=1.0.19
# RUN curl -L -O "https://download.libsodium.org/libsodium/releases/libsodium-${LIBSODIUM_VERSION}.tar.gz" \
#  && tar -xzf libsodium-${LIBSODIUM_VERSION}.tar.gz \
#  && mv libsodium-stable libsodium \
#  && rm libsodium*.tar.gz
#
# WORKDIR /src/libsodium
# RUN ./configure --prefix="${HOST_PREFIX}" --host=$HOST
# RUN make -j4
# RUN make install
#
# # build libzmq
# WORKDIR /src
# ENV LIBZMQ_VERSION=4.3.5
# RUN curl -L -O "https://github.com/zeromq/libzmq/releases/download/v${LIBZMQ_VERSION}/zeromq-${LIBZMQ_VERSION}.tar.gz" \
#  && tar -xzf zeromq-${LIBZMQ_VERSION}.tar.gz \
#  && mv zeromq-${LIBZMQ_VERSION} zeromq
# WORKDIR /src/zeromq
# RUN ./configure --prefix="$HOST_PREFIX" --host=$HOST --disable-perf --disable-Werror --without-docs --enable-curve --with-libsodium=$HOST_PREFIX --disable-drafts --disable-libsodium_randombytes_close
# RUN make -j4
# RUN make install

# setup crossenv
WORKDIR /src
ENV CROSS_PREFIX=/opt/cross
RUN python3 -m pip install crossenv \
 && python3 -m crossenv ${HOST_PREFIX}/bin/python3 ${CROSS_PREFIX}
ENV PATH=${CROSS_PREFIX}/bin:$PATH

# install build dependencies in crossenv
RUN . ${CROSS_PREFIX}/bin/activate \
 && build-pip install build pyproject_metadata scikit-build-core pathspec cython

# if pyzmq is bundling libsodium, tell it to cross-compile
# not required if libzmq is already installed
ENV PYZMQ_LIBSODIUM_CONFIGURE_ARGS="--host $HOST"
ARG PYZMQ_VERSION=26.0.0b2
# build wheel of pyzmq
WORKDIR /src
RUN python3 -m pip download --no-binary pyzmq --pre pyzmq==$PYZMQ_VERSION \
 && tar -xzf pyzmq-*.tar.gz \
 && rm pyzmq-*.tar.gz \
 && . ${CROSS_PREFIX}/bin/activate \
 && cross-python -m build --no-isolation --skip-dependency-check --wheel ./pyzmq*

# there is now a pyzmq wheel in /src/pyzmq-$version/dist/pyzmq-$VERSION-cp311-cp311-linux_x86_64.whl
