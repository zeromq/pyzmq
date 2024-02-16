# 3.28 needed for EXCLUDE_FROM_ALL
cmake_minimum_required(VERSION 3.28)
project(${SKBUILD_PROJECT_NAME} LANGUAGES C CXX)
set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)

list(PREPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
find_package(
  Python
  COMPONENTS Interpreter Development.Module
  REQUIRED)

set(ZMQ_PREFIX "auto" CACHE STRING "libzmq installation prefix or 'bundled'")
option(ZMQ_DRAFT_API "whether to build the libzmq draft API" OFF)
set(LIBZMQ_BUNDLED_VERSION "4.3.5" CACHE STRING "libzmq version when bundling")
set(LIBSODIUM_BUNDLED_VERSION "1.0.19" CACHE STRING "libsodium version when bundling")
set(LIBZMQ_BUNDLED_URL "" CACHE STRING "full URL to download bundled libzmq")
set(LIBSODIUM_BUNDLED_URL "" CACHE STRING "full URL to download bundled libsodium")
set(LIBSODIUM_CONFIGURE_ARGS "" CACHE STRING "semicolon-separated list of arguments to pass to ./configure for bundled libsodium")
set(LIBSODIUM_MSBUILD_ARGS "" CACHE STRING "semicolon-separated list of arguments to pass to msbuild for bundled libsodium")
set(LIBSODIUM_VS_VERSION "" CACHE STRING "Visual studio solution version for bundled libsodium (default: detect from MSVC_VERSION)")

if (NOT CMAKE_BUILD_TYPE)
  # default to Release
  set(CMAKE_BUILD_TYPE "Release")
endif()

# get options from env
if (DEFINED ENV{ZMQ_PREFIX})
  set(ZMQ_PREFIX "$ENV{ZMQ_PREFIX}")
endif()

if (DEFINED ENV{ZMQ_DRAFT_API})
  if ("$ENV{ZMQ_DRAFT_API}" STREQUAL "1")
    set(ZMQ_DRAFT_API TRUE)
  else()
    set(ZMQ_DRAFT_API FALSE)
  endif()
endif()

# load options from env with PYZMQ_ prefix
foreach(_optname
  LIBZMQ_BUNDLED_VERSION
  LIBZMQ_BUNDLED_URL
  LIBSODIUM_BUNDLED_VERSION
  LIBSODIUM_BUNDLED_URL
  LIBSODIUM_CONFIGURE_ARGS
  LIBSODIUM_MSBUILD_ARGS
  LIBSODIUM_VS_VERSION
)
  if (DEFINED ENV{PYZMQ_${_optname}})
    if (_optname MATCHES ".*_ARGS")
      # if it's an _ARGS, split "-a -b" into "-a" "-b"
      # use native CMake lists for cmake args,
      # native command-line strings for env variables
      separate_arguments(${_optname} NATIVE_COMMAND "$ENV{PYZMQ_${_optname}}")
    else()
      set(${_optname} "$ENV{PYZMQ_${_optname}}")
    endif()
  endif()
endforeach()

if(ZMQ_DRAFT_API)
  message(STATUS "enabling ZMQ_DRAFT_API")
  add_compile_definitions(ZMQ_BUILD_DRAFT_API=1)
endif()

if (LIBSODIUM_BUNDLED_VERSION AND NOT LIBSODIUM_BUNDLED_URL)
  set(LIBSODIUM_BUNDLED_URL "https://download.libsodium.org/libsodium/releases/libsodium-${LIBSODIUM_BUNDLED_VERSION}.tar.gz")
endif()

if (LIBZMQ_BUNDLED_VERSION AND NOT LIBZMQ_BUNDLED_URL)
  set(LIBZMQ_BUNDLED_URL "https://github.com/zeromq/libzmq/releases/download/v${LIBZMQ_BUNDLED_VERSION}/zeromq-${LIBZMQ_BUNDLED_VERSION}.tar.gz")
endif()

#------- bundle libzmq ------

if (NOT ZMQ_PREFIX)
  # empty string is the same as 'auto'
  set(ZMQ_PREFIX "auto")
endif()

# default search paths:

foreach(prefix $ENV{PREFIX} "/opt/homebrew" "/opt/local" "/usr/local" "/usr")
  if (IS_DIRECTORY "${prefix}")
    list(APPEND CMAKE_PREFIX_PATH "${prefix}")
  endif()
endforeach()

if (ZMQ_PREFIX STREQUAL "auto")
  message(CHECK_START "Looking for libzmq")
  find_package(ZeroMQ QUIET)
  if (ZeroMQ_FOUND AND TARGET libzmq)
    set(libzmq_target "libzmq")
    get_target_property(_ZMQ_LOCATION libzmq IMPORTED_LOCATION)
    message(CHECK_PASS "Found with cmake: ${_ZMQ_LOCATION}")
  endif()

  if (NOT ZeroMQ_FOUND)
    find_package(PkgConfig QUIET)
    if (PkgConfig_FOUND)
      message(CHECK_START "Looking for libzmq with pkg-config")
      pkg_check_modules(libzmq libzmq IMPORTED_TARGET)
      if (TARGET PkgConfig::libzmq)
        set(ZeroMQ_FOUND TRUE)
        set(libzmq_target "PkgConfig::libzmq")
        message(CHECK_PASS "found: -L${libzmq_LIBRARY_DIRS} -l${libzmq_LIBRARIES}")
      else()
        message(CHECK_FAIL "no")
      endif()
    endif()
  endif()

  if (NOT ZeroMQ_FOUND)
    message(STATUS "  Fallback: looking for libzmq in ${CMAKE_PREFIX_PATH}")
    find_library(LIBZMQ_LIBRARY NAMES zmq)
    find_path(LIBZMQ_INCLUDE_DIR "zmq.h")

    # check if found
    if (LIBZMQ_LIBRARY AND LIBZMQ_INCLUDE_DIR)
      set(ZeroMQ_FOUND TRUE)
      message(CHECK_PASS "${LIBZMQ_LIBRARY}")
    endif()
  endif()

  if (NOT ZeroMQ_FOUND)
    message(CHECK_FAIL "libzmq not found, will bundle libzmq and libsodium")
    set(ZMQ_PREFIX "bundled")
  endif()
elseif (NOT ZMQ_PREFIX STREQUAL "bundled")
  message(CHECK_START "Looking for libzmq in ${ZMQ_PREFIX}")
  find_path(
    LIBZMQ_INCLUDE_DIR zmq.h
    PATHS "${ZMQ_PREFIX}/include"
    NO_DEFAULT_PATH
  )
  find_library(
    LIBZMQ_LIBRARY
    NAMES zmq
    PATHS "${ZMQ_PREFIX}/lib"
    NO_DEFAULT_PATH
  )
  if (LIBZMQ_LIBRARY AND LIBZMQ_INCLUDE_DIR)
    message(CHECK_PASS "${LIBZMQ_LIBRARY}")
  else()
    message(CHECK_FAIL "no")
    message(FATAL_ERROR "libzmq not found in ZMQ_PREFIX=${ZMQ_PREFIX}")
  endif()
else()
  # bundled
endif()

if (ZMQ_PREFIX STREQUAL "bundled")
  message(STATUS "Bundling libzmq and libsodium")
  include(FetchContent)
  add_compile_definitions(ZMQ_STATIC=1)
  set(BUNDLE_DIR "${CMAKE_CURRENT_BINARY_DIR}/bundled")
  make_directory("${BUNDLE_DIR}/lib")
  include_directories(${BUNDLE_DIR}/include)
  list(PREPEND CMAKE_PREFIX_PATH ${BUNDLE_DIR})

  # libsodium

  if (MSVC)
    set(libsodium_lib "${BUNDLE_DIR}/lib/libsodium.lib")
  else()
    set(libsodium_lib "${BUNDLE_DIR}/lib/libsodium.a")
  endif()

  FetchContent_Declare(bundled_libsodium
    URL ${LIBSODIUM_BUNDLED_URL}
    PREFIX ${BUNDLE_DIR}
  )
  FetchContent_MakeAvailable(bundled_libsodium)
  # run libsodium build explicitly here, so it's available to libzmq next
  set(bundled_libsodium_include "${bundled_libsodium_SOURCE_DIR}/src/libsodium/include")

  if(${bundled_libsodium_POPULATED} AND NOT EXISTS "${libsodium_lib}")
    message(STATUS "building bundled libsodium")
    if (MSVC)
      # select vs build solution by msvc version number
      if (NOT LIBSODIUM_VS_VERSION)
        if(MSVC_VERSION GREATER 1940)
          message(STATUS "Unrecognized MSVC_VERSION=${MSVC_VERSION}")
          set(MSVC_VERSION 1939)
        endif()

        if(MSVC_VERSION GREATER_EQUAL 1930)
          set(LIBSODIUM_VS_VERSION "2022")
        elseif(MSVC_VERSION GREATER_EQUAL 1920)
          set(LIBSODIUM_VS_VERSION "2019")
        elseif(MSVC_VERSION GREATER_EQUAL 1910)
          set(LIBSODIUM_VS_VERSION "2017")
        else()
          message(FATAL_ERROR "unsupported bundling libsodium for MSVC_VERSION=${MSVC_VERSION} (need at least VS2017)")
        endif()
      endif()
      find_package(Vcvars REQUIRED)
      list(APPEND libsodium_build
        ${Vcvars_LAUNCHER}
        "msbuild"
        "/m"
        "/v:n"
        "/p:Configuration=Static${CMAKE_BUILD_TYPE}"
        "/p:Platform=${CMAKE_GENERATOR_PLATFORM}"
        "builds/msvc/vs${LIBSODIUM_VS_VERSION}/libsodium.sln"
      )
      list(APPEND libsodium_build ${LIBSODIUM_MSBUILD_ARGS})
      execute_process(
        COMMAND ${libsodium_build}
        WORKING_DIRECTORY ${bundled_libsodium_SOURCE_DIR}
        COMMAND_ECHO STDOUT
        COMMAND_ERROR_IS_FATAL ANY
      )
      file(GLOB_RECURSE BUILT_LIB "${bundled_libsodium_SOURCE_DIR}/**/libsodium.lib")
      message(STATUS "copy ${BUILT_LIB} ${libsodium_lib}")
      file(COPY_FILE ${BUILT_LIB} ${libsodium_lib})
    else()
      list(APPEND libsodium_configure
        ./configure
        --prefix=${BUNDLE_DIR}
        --with-pic
        --disable-shared
        --enable-static
      )
      list(APPEND libsodium_configure ${LIBSODIUM_CONFIGURE_ARGS})
      execute_process(
        COMMAND ${libsodium_configure}
        WORKING_DIRECTORY ${bundled_libsodium_SOURCE_DIR}
        COMMAND_ECHO      STDOUT
        COMMAND_ERROR_IS_FATAL ANY
      )
      execute_process(
        COMMAND make
        WORKING_DIRECTORY ${bundled_libsodium_SOURCE_DIR}
        COMMAND_ECHO STDOUT
        COMMAND_ERROR_IS_FATAL ANY
      )
      execute_process(
        COMMAND make install
        WORKING_DIRECTORY ${bundled_libsodium_SOURCE_DIR}
        COMMAND_ECHO STDOUT
        COMMAND_ERROR_IS_FATAL ANY
      )
    endif()
  endif()

  # use libzmq's own cmake, so we can import the libzmq-static target
  set(ENABLE_CURVE ON)
  set(ENABLE_DRAFTS ${ZMQ_DRAFT_API})
  set(WITH_LIBSODIUM ON)
  set(WITH_LIBSODIUM_STATIC ON)
  set(LIBZMQ_PEDANTIC OFF)
  set(LIBZMQ_WERROR OFF)
  set(WITH_DOC OFF)
  set(WITH_DOCS OFF)
  set(BUILD_TESTS OFF)
  set(BUILD_SHARED OFF)
  set(BUILD_STATIC ON)

  FetchContent_Declare(bundled_libzmq
    URL ${LIBZMQ_BUNDLED_URL}
    PREFIX ${BUNDLE_DIR}
    CMAKE_ARGS ${LIBZMQ_CMAKE_ARGS}
    EXCLUDE_FROM_ALL
  )
  FetchContent_MakeAvailable(bundled_libzmq)

  # target for libzmq static
  if (TARGET libzmq-static)
    set(libzmq_target "libzmq-static")
  else()
    message(FATAL_ERROR "libzmq-static target not found in bundled libzmq")
  endif()
endif()

if (NOT TARGET "${libzmq_target}" AND LIBZMQ_LIBRARY AND LIBZMQ_INCLUDE_DIR)
  set(libzmq_target "libzmq")
  # construct target from find_library results
  # what if it was static?
  add_library(libzmq SHARED IMPORTED)
  set_property(TARGET libzmq PROPERTY IMPORTED_LOCATION ${LIBZMQ_LIBRARY})
  set_property(TARGET libzmq PROPERTY INTERFACE_INCLUDE_DIRECTORIES ${LIBZMQ_INCLUDE_DIR})
endif()

#------- building pyzmq itself -------

message(STATUS "Using Python ${Python_INTERPRETER_ID} ${Python_EXECUTABLE}")

set(ZMQ_BACKEND "${CMAKE_CURRENT_BINARY_DIR}/zmq/backend")
set(ZMQ_BUILDUTILS "${CMAKE_CURRENT_SOURCE_DIR}/buildutils")

if(Python_INTERPRETER_ID STREQUAL "PyPy")
  message(STATUS "Building CFFI backend")
  set(ZMQ_EXT_NAME "_cffi")

  set(ZMQ_BACKEND_CFFI "${ZMQ_BACKEND}/cffi")
  set(ZMQ_BACKEND_DEST "zmq/backend/cffi")
  set(ZMQ_C "${ZMQ_BACKEND_CFFI}/${ZMQ_EXT_NAME}.c")

  add_custom_command(
    OUTPUT ${ZMQ_C}
    VERBATIM
    COMMAND "${Python_EXECUTABLE}"
            "${ZMQ_BUILDUTILS}/build_cffi.py"
            "${ZMQ_C}"
  )
else()
  message(STATUS "Building Cython backend")
  find_program(CYTHON "cython")

  set(ZMQ_BACKEND_CYTHON "${ZMQ_BACKEND}/cython")
  set(ZMQ_BACKEND_DEST "zmq/backend/cython")
  set(ZMQ_EXT_NAME "_zmq")
  set(ZMQ_C "${ZMQ_BACKEND_CYTHON}/${ZMQ_EXT_NAME}.c")
  set(ZMQ_PYX "${CMAKE_CURRENT_SOURCE_DIR}/zmq/backend/cython/${ZMQ_EXT_NAME}.py")
  add_custom_command(
    OUTPUT ${ZMQ_C}
    DEPENDS ${ZMQ_PYX}
    VERBATIM
    COMMAND "${CYTHON}"
            --3str
            --output-file ${ZMQ_C}
            ${ZMQ_PYX}
  )
endif()

make_directory(${ZMQ_BACKEND_DEST})

python_add_library(
  ${ZMQ_EXT_NAME} MODULE
  WITH_SOABI
  ${ZMQ_C}
)

if (TARGET ${libzmq_target})
  message(STATUS "Linking libzmq target ${libzmq_target}")
  target_link_libraries(${ZMQ_EXT_NAME} PUBLIC ${libzmq_target})
  if ("${libzmq_target}" STREQUAL "libzmq-static" AND NOT MSVC)
    # seem to need stdc++ for static libzmq on non-Windows
    # not sure if/when this should be libc++ or how to know
    target_link_libraries(${ZMQ_EXT_NAME} PUBLIC stdc++)
  endif()
else()
  message(FATAL_ERROR "should have a libzmq target ${libzmq_target} to link to...")
endif()

target_include_directories(${ZMQ_EXT_NAME} PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/zmq/utils")
install(TARGETS ${ZMQ_EXT_NAME} DESTINATION "${ZMQ_BACKEND_DEST}")
