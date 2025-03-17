#!/usr/bin/env bash
# script to install libzmq/libsodium for use in wheels
set -ex
LIBSODIUM_VERSION=$(python buildutils/bundle.py libsodium)
LIBZMQ_VERSION=$(python buildutils/bundle.py)
PYZMQ_DIR="$PWD"
LICENSE_DIR="$PYZMQ_DIR/licenses"
test -d "$LICENSE_DIR" || mkdir "$LICENSE_DIR"

if [[ "$(uname)" == "Darwin" ]]; then
    # make sure deployment target is set
    echo "${MACOSX_DEPLOYMENT_TARGET=}"
    test ! -z "${MACOSX_DEPLOYMENT_TARGET}"
    # need LT_MULTI_MODULE or libtool will strip out
    # all multi-arch symbols at the last step
    export LT_MULTI_MODULE=1
    ARCHS="x86_64"
    case "${CIBW_ARCHS_MACOS:-${CIBW_ARCHS:-auto}}" in
        "universal2")
            ARCHS="x86_64 arm64"
            ;;
        "arm64")
            ARCHS="arm64"
            ;;
        "x86_64")
            ARCHS="x86_64"
            ;;
        "auto")
            ;;
        *)
            echo "Unexpected arch: ${CIBW_ARCHS_MACOS}"
            exit 1
            ;;
    esac
    echo "building libzmq for mac ${ARCHS}"
    export CXX="${CC:-clang++}"
    for arch in ${ARCHS}; do
        # seem to need ARCH in CXX for libtool
        export CXX="${CXX} -arch ${arch}"
        export CFLAGS="-arch ${arch} ${CFLAGS:-}"
        export CXXFLAGS="-arch ${arch} ${CXXFLAGS:-}"
        export LDFLAGS="-arch ${arch} ${LDFLAGS:-}"
    done
fi

PREFIX="${ZMQ_PREFIX:-/usr/local}"
# add rpath so auditwheel patches it
export LDFLAGS="${LDFLAGS} -Wl,-rpath,$PREFIX/lib"

curl -L -O "https://github.com/jedisct1/libsodium/releases/download/${LIBSODIUM_VERSION}-RELEASE/libsodium-${LIBSODIUM_VERSION}.tar.gz"

curl -L -O "https://github.com/zeromq/libzmq/releases/download/v${LIBZMQ_VERSION}/zeromq-${LIBZMQ_VERSION}.tar.gz"

tar -xzf libsodium-${LIBSODIUM_VERSION}.tar.gz
cd libsodium-*/
cp LICENSE "${LICENSE_DIR}/LICENSE.libsodium.txt"
./configure --prefix="$PREFIX"
make -j4
make install

cd ..

which ldconfig && ldconfig || true

# make sure to find our libsodium
export PKG_CONFIG_PATH=$PREFIX/lib/pkgconfig

tar -xzf zeromq-${LIBZMQ_VERSION}.tar.gz
cd zeromq-${LIBZMQ_VERSION}
cp LICENSE "${LICENSE_DIR}/LICENSE.zeromq.txt"
# avoid error on warning
export CXXFLAGS="-Wno-error ${CXXFLAGS:-}"

./configure --prefix="$PREFIX" --disable-perf --without-docs --enable-curve --with-libsodium --disable-drafts --disable-libsodium_randombytes_close
make -j4
make install

which ldconfig && ldconfig || true
