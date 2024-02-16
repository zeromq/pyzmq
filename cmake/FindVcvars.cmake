# unmodified from: https://raw.githubusercontent.com/scikit-build/cmake-FindVcvars/v1.6/FindVcvars.cmake

# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

#[=======================================================================[.rst:
FindVcvars
----------

Finds a "vcvars" batch script.

The module can be used when configuring a project or when running
in cmake -P script mode.

These variables can be used to choose which "vcvars" batch script is looked up.

.. variable:: Vcvars_MSVC_ARCH

  Possible values are `32` or `64`

  If not explicitly set in the calling scope, the variable is initialized
  based on the value of :variable:`CMAKE_SIZEOF_VOID_P` in configuration mode, and
  to 64 in script mode.

.. variable:: Vcvars_MSVC_VERSION

  Possible values corresponds to :variable:`MSVC_VERSION`.

  If not explicitly set in the calling scope, :variable:`Vcvars_MSVC_VERSION` is
  initialized using :variable:`MSVC_VERSION` variable if it is defined, otherwise
  the variable :variable:`Vcvars_MSVC_VERSION` is initialized based on the most
  recent version of Visual Studio installed on the system.

This will define the following variables:

.. variable:: Vcvars_BATCH_FILE

  Path to ``vcvars32.bat``, ``vcvarsamd64.bat`` or ``vcvars64.bat``.

.. variable:: Vcvars_LAUNCHER

  Path to a generated wrapper script allowing to execute program after
  setting environment defined by `Vcvars_BATCH_FILE`.

  It can be used within :module:`ExternalProject` steps
  specifying command like this::

    set(cmd_wrapper)
    if(MSVC)
      find_package(Vcvars REQUIRED)
      set(cmd_wrapper ${Vcvars_LAUNCHER})
    endif()

    ExternalProject_Add(AwesomeProject
      [...]
      BUILD_COMMAND ${cmd_wrapper} <command> arg1 arg2 [...]
      [...]
      )

This module also defines the following functions


.. command:: Vcvars_GetVisualStudioPaths

  The ``Vcvars_GetVisualStudioPaths()`` function returns a list of all
  possible Visual Studio registry paths associated with a given ``<msvc_version>``
  and ``<msvc_arch>``::

    Vcvars_GetVisualStudioPaths(<msvc_version> <msvc_arch> <output_var>)

  The options are:

  ``<msvc_version>``
    Specify the Visual Studio compiler version. See :variable:`MSVC_VERSION`
    for possible values.

  ``<msvc_arch>``
    Specify the Visual Studio architecture. Possible values are `32` or `64`.

  ``<output_var>``
    The name of the variable to be set with the list of registry paths.


.. command:: Vcvars_ConvertMsvcVersionToVsVersion

  The ``Vcvars_ConvertMsvcVersionToVsVersion()`` function converts a
  :variable:`MSVC_VERSION` of the form ``NNNN`` to a Visual Studio version
  of the form ``XX.Y`::

    Vcvars_ConvertMsvcVersionToVsVersion(<msvc_version> <output_var>)

  The options are:

  ``<msvc_version>``
    Specify the Visual Studio compiler version. See :variable:`MSVC_VERSION`
    for possible values.

  ``<output_var>``
    The name of the variable to be set with the Visual Studio version.

#]=======================================================================]

cmake_minimum_required(VERSION 3.5)

# Global variables used only in this script (unset at the end)
set(_Vcvars_MSVC_ARCH_REGEX "^(32|64)$")
set(_Vcvars_MSVC_VERSION_REGEX "^[0-9][0-9][0-9][0-9]$")
set(_Vcvars_SUPPORTED_MSVC_VERSIONS
  1939 1938 1937 1936 1935 1934 1933 1932 1931 1930 # VS 2022
  1929 1928 1927 1926 1925 1924 1923 1922 1921 1920 # VS 2019
  1916 1915 1914 1913 1912 1911 1910 # VS 2017
  1900 # VS 2015
  1800 # VS 2013
  1700 # VS 2012
  1600 # VS 2010
  1500 # VS 2008
  1400 # VS 2005
  )

function(_vcvars_message)
  if(NOT Vcvars_FIND_QUIETLY)
    message(${ARGN})
  endif()
endfunction()

function(Vcvars_ConvertMsvcVersionToVsVersion msvc_version output_var)
  if(NOT msvc_version MATCHES ${_Vcvars_MSVC_VERSION_REGEX})
    message(FATAL_ERROR "msvc_version is expected to match `${_Vcvars_MSVC_VERSION_REGEX}`")
  endif()
  # See https://en.wikipedia.org/wiki/Microsoft_Visual_C%2B%2B#Internal_version_numbering
  if((msvc_version GREATER_EQUAL 1930) AND (msvc_version LESS 1940))     # VS 2022
    set(vs_version "17")
  elseif((msvc_version GREATER_EQUAL 1920) AND (msvc_version LESS 1930)) # VS 2019
    set(vs_version "16")
  elseif((msvc_version GREATER_EQUAL 1910) AND (msvc_version LESS 1920)) # VS 2017
    set(vs_version "15")
  elseif(msvc_version EQUAL 1900) # VS 2015
    set(vs_version "14.0")
  elseif(msvc_version EQUAL 1800) # VS 2013
    set(vs_version "12.0")
  elseif(msvc_version EQUAL 1700) # VS 2012
    set(vs_version "11.0")
  elseif(msvc_version EQUAL 1600) # VS 2010
    set(vs_version "10.0")
  elseif(msvc_version EQUAL 1500) # VS 2008
    set(vs_version "9.0")
  elseif(msvc_version EQUAL 1400) # VS 2005
    set(vs_version "8.0")
  elseif(msvc_version EQUAL 1310) # VS 2003
    set(vs_version "7.1")
  elseif(msvc_version EQUAL 1300) # VS 2002
    set(vs_version "7.0")
  elseif(msvc_version EQUAL 1200) # VS 6.0
    set(vs_version "6.0")
  else()
    message(FATAL_ERROR "failed to convert msvc_version [${msvc_version}]. It is not a known version number.")
  endif()
  set(${output_var} ${vs_version} PARENT_SCOPE)
endfunction()

function(Vcvars_GetVisualStudioPaths msvc_version msvc_arch output_var)

  if(NOT msvc_version MATCHES ${_Vcvars_MSVC_VERSION_REGEX})
    message(FATAL_ERROR "msvc_version is expected to match `${_Vcvars_MSVC_VERSION_REGEX}`")
  endif()

  if(NOT msvc_arch MATCHES ${_Vcvars_MSVC_ARCH_REGEX})
    message(FATAL_ERROR "msvc_arch argument is expected to match '${_Vcvars_MSVC_ARCH_REGEX}'")
  endif()

  Vcvars_ConvertMsvcVersionToVsVersion(${msvc_version} vs_version)

  set(_vs_installer_paths "")
  set(_vs_registry_paths "")
  if(vs_version VERSION_GREATER_EQUAL "15.0")
    # Query the VS Installer tool for locations of VS 2017 and above.
    string(REGEX REPLACE "^([0-9]+)\.[0-9]+$" "\\1" vs_installer_version ${vs_version})
    cmake_host_system_information(RESULT _vs_dir QUERY VS_${vs_installer_version}_DIR)
    if(_vs_dir)
      list(APPEND _vs_installer_paths "${_vs_dir}/VC/Auxiliary/Build")
    endif()
  else()
    # Registry keys for locations of VS 2015 and below
    set(_hkeys
      "HKEY_USERS"
      "HKEY_CURRENT_USER"
      "HKEY_LOCAL_MACHINE"
      "HKEY_CLASSES_ROOT"
      )
    set(_suffixes
      ""
      "_Config"
      )
    set(_arch_path "bin/amd64")
    if(msvc_arch STREQUAL "32")
      set(_arch_path "bin")
    endif()
    set(_vs_registry_paths)
    foreach(_hkey IN LISTS _hkeys)
      foreach(_suffix IN LISTS _suffixes)
        set(_vc "VC")
        if(_vs_version STREQUAL "6.0")
          set(_vc "Microsoft Visual C++")
        endif()
        list(APPEND _vs_registry_paths
          "[${_hkey}\\SOFTWARE\\Microsoft\\VisualStudio\\${vs_version}${_suffix}\\Setup\\${_vc};ProductDir]/${_arch_path}"
          )
      endforeach()
    endforeach()
  endif()
  set(_vs_installer_paths ${_vs_installer_paths} ${_vs_registry_paths})
  if(_vs_installer_paths STREQUAL "")
    set(_vs_installer_paths "${output_var}-${msvc_version}-${msvc_arch}-NOTFOUND")
  endif()
  set(${output_var} ${_vs_installer_paths} PARENT_SCOPE)
endfunction()

# default
if(NOT DEFINED Vcvars_MSVC_ARCH)
  if(NOT DEFINED CMAKE_SIZEOF_VOID_P)
    set(Vcvars_MSVC_ARCH "64")
    _vcvars_message(STATUS "Setting Vcvars_MSVC_ARCH to '${Vcvars_MSVC_ARCH}' as CMAKE_SIZEOF_VOID_P was none")
  else()
    if("${CMAKE_SIZEOF_VOID_P}" EQUAL 4)
      set(Vcvars_MSVC_ARCH "32")
    elseif("${CMAKE_SIZEOF_VOID_P}" EQUAL 8)
      set(Vcvars_MSVC_ARCH "64")
    else()
      message(FATAL_ERROR "CMAKE_SIZEOF_VOID_P [${CMAKE_SIZEOF_VOID_P}] is expected to be either 4 or 8")
    endif()
    # Display message only once in config mode
    if(NOT DEFINED Vcvars_BATCH_FILE)
      _vcvars_message(STATUS "Setting Vcvars_MSVC_ARCH to '${Vcvars_MSVC_ARCH}' as CMAKE_SIZEOF_VOID_P was `${CMAKE_SIZEOF_VOID_P}`")
    endif()
  endif()
endif()

if(NOT DEFINED Vcvars_MSVC_VERSION)
  if(DEFINED MSVC_VERSION)
    set(Vcvars_MSVC_VERSION ${MSVC_VERSION})
    # Display message only once in config mode
    if(NOT DEFINED Vcvars_BATCH_FILE)
      _vcvars_message(STATUS "Setting Vcvars_MSVC_VERSION to '${Vcvars_MSVC_VERSION}' as MSVC_VERSION was `${MSVC_VERSION}`")
    endif()
  endif()
endif()
if(NOT DEFINED Vcvars_BATCH_FILE)
  set(Vcvars_BATCH_FILE "Vcvars_BATCH_FILE-NOTFOUND")
endif()
if(NOT DEFINED Vcvars_LAUNCHER)
  set(Vcvars_LAUNCHER "Vcvars_LAUNCHER-NOTFOUND")
endif()

# check Vcvars_MSVC_ARCH is properly set
if(NOT Vcvars_MSVC_ARCH MATCHES ${_Vcvars_MSVC_ARCH_REGEX})
  message(FATAL_ERROR "Vcvars_MSVC_ARCH [${Vcvars_MSVC_ARCH}] is expected to match `${_Vcvars_MSVC_ARCH_REGEX}`")
endif()

# which vcvars script ?
if(Vcvars_MSVC_ARCH STREQUAL "64")
  set(_Vcvars_SCRIPTS vcvarsamd64.bat vcvars64.bat)
else()
  set(_Vcvars_SCRIPTS vcvars32.bat)
endif()

# set Vcvars_BATCH_FILE
if(NOT DEFINED Vcvars_MSVC_VERSION)
  # auto-discover Vcvars_MSVC_VERSION value
  _vcvars_message(STATUS "Setting Vcvars_MSVC_VERSION")
  foreach(_candidate_msvc_version IN LISTS _Vcvars_SUPPORTED_MSVC_VERSIONS)
    Vcvars_GetVisualStudioPaths(${_candidate_msvc_version} "${Vcvars_MSVC_ARCH}" _paths)
    Vcvars_ConvertMsvcVersionToVsVersion(${_candidate_msvc_version} _candidate_vs_version)
    set(_msg "  Visual Studio ${_candidate_vs_version} (${_candidate_msvc_version})")
    _vcvars_message(STATUS "${_msg}")
    find_program(Vcvars_BATCH_FILE NAMES ${_Vcvars_SCRIPTS}
      DOC "Visual Studio ${_candidate_vs_version} ${_Vcvars_SCRIPTS}"
      PATHS ${_paths}
      )
    if(Vcvars_BATCH_FILE)
      _vcvars_message(STATUS "${_msg} - found")
      set(Vcvars_MSVC_VERSION ${_candidate_msvc_version})
      _vcvars_message(STATUS "Setting Vcvars_MSVC_VERSION to '${Vcvars_MSVC_VERSION}' as it was the newest Visual Studio installed providing vcvars scripts")
      break()
    else()
      _vcvars_message(STATUS "${_msg} - not found")
    endif()
  endforeach()
  unset(_candidate_msvc_version)
  unset(_candidate_vs_version)
  unset(_paths)
else()
  # use provided Vcvars_MSVC_VERSION value
  if(NOT Vcvars_MSVC_VERSION MATCHES ${_Vcvars_MSVC_VERSION_REGEX})
    message(FATAL_ERROR "Vcvars_MSVC_VERSION [${Vcvars_MSVC_VERSION}] is expected to match `${_Vcvars_MSVC_VERSION_REGEX}`")
  endif()
  Vcvars_GetVisualStudioPaths(${Vcvars_MSVC_VERSION} "${Vcvars_MSVC_ARCH}" _paths)
  Vcvars_ConvertMsvcVersionToVsVersion(${Vcvars_MSVC_VERSION} _vs_version)
  find_program(Vcvars_BATCH_FILE NAMES ${_Vcvars_SCRIPTS}
    DOC "Visual Studio ${_vs_version} ${_Vcvars_SCRIPTS}"
    PATHS ${_paths}
    )
  unset(_paths)
  unset(_vs_version)
endif()

# configure wrapper script
set(Vcvars_LAUNCHER)
if(Vcvars_BATCH_FILE)

  set(_in "${CMAKE_BINARY_DIR}/${CMAKE_FILES_DIRECTORY}/Vcvars_wrapper.bat.in")
  get_filename_component(_basename ${Vcvars_BATCH_FILE} NAME_WE)
  set(_out "${CMAKE_BINARY_DIR}/${CMAKE_FILES_DIRECTORY}/${_basename}_wrapper.bat")
  file(WRITE ${_in} "call \"@Vcvars_BATCH_FILE@\"
%*
")
  configure_file(${_in} ${_out} @ONLY)

  set(Vcvars_LAUNCHER ${_out})
  unset(_in)
  unset(_out)
endif()

# cleanup
unset(_Vcvars_SCRIPTS)

# outputs
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Vcvars
  FOUND_VAR Vcvars_FOUND
  REQUIRED_VARS
    Vcvars_BATCH_FILE
    Vcvars_LAUNCHER
    Vcvars_MSVC_VERSION
    Vcvars_MSVC_ARCH
  FAIL_MESSAGE
    "Failed to find vcvars scripts for Vcvars_MSVC_VERSION [${Vcvars_MSVC_VERSION}] and Vcvars_MSVC_ARCH [${Vcvars_MSVC_ARCH}]"
  )
