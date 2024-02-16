# copy libzmq's findsodium, which can't be told where to look
# we want to get our local bundled static libsodium
# not any other
message(CHECK_START "Looking for pyzmq-bundled libsodium")
set(SODIUM_FOUND FALSE)

set(PKG_CONFIG_USE_CMAKE_PREFIX_PATH ON)
find_package(PkgConfig QUIET)
if (PkgConfig_FOUND)
  pkg_check_modules(PC_SODIUM "libsodium")
  if (PC_SODIUM_STATIC_FOUND)
    set(pkg_config_names_private "${pkg_config_names_private} libsodium")
    set(SODIUM_LIBRARIES ${PC_SODIUM_STATIC_LIBRARIES})
    set(SODIUM_INCLUDE_DIRS ${PC_SODIUM_STATIC_INCLUDE_DIRS})
    set(SODIUM_FOUND TRUE)
  endif()
endif()

if (NOT SODIUM_FOUND)
  set(SODIUM_INCLUDE_DIRS ${bundled_libsodium_include})
  find_library(
      SODIUM_LIBRARIES
      NAMES libsodium.a libsodium.lib
      PATH ${BUNDLE_DIR}/lib
  )
  message(STATUS "Found bundled ${SODIUM_LIBRARIES} in ${BUNDLE_DIR}")
  if (SODIUM_LIBRARIES)
    # pkg-config didn't work, what do we need?
    if (NOT MSVC)
      list(APPEND SODIUM_LIBRARIES pthread)
    endif()
    set(SODIUM_FOUND TRUE)
  endif()
endif()

if (NOT SODIUM_FOUND)
  message(CHECK_FAIL "no")
  message(FATAL_ERROR "Failed to find bundled libsodium")
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(sodium DEFAULT_MSG SODIUM_LIBRARIES SODIUM_INCLUDE_DIRS)
mark_as_advanced(SODIUM_FOUND SODIUM_LIBRARIES SODIUM_INCLUDE_DIRS)
