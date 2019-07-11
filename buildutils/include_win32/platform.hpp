// copied from libzmq 4.2.3
// has been removed since then
// included under LGPLv3

#ifndef __PLATFORM_HPP_INCLUDED__
#define __PLATFORM_HPP_INCLUDED__

#define ZMQ_HAVE_WINDOWS

// MSVC build configuration is controlled via options exposed in the Visual
// Studio user interface. The option to use libsodium is not exposed in the
// user interface unless a sibling `libsodium` directory to that of this
// repository exists and contains the following files:
//
// \builds\msvc\vs2015\libsodium.import.props
// \builds\msvc\vs2015\libsodium.import.xml

// additional defines required for 4.3 after this file was removed
#define ZMQ_USE_SELECT 1
#define ZMQ_IOTHREAD_POLLER_USE_SELECT 1
#define ZMQ_POLL_BASED_ON_SELECT 1
#define ZMQ_USE_CV_IMPL_WIN32API 1

#endif
