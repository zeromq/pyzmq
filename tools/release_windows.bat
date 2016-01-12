@echo off
REM build a pyzmq release on Windows
REM 32+64b eggs on Python 27, and wheels on 27, 34, 35
REM that's 10 bdists
REM requires Windows SDK 7.0 (for py2) and 7.1 (for py3), and VS2015C for py3.5
REM and Python installed in the locations: C:\Python34 (32b) and C:\Python34_64 (64b)
REM after running, upload with `twine upload dist/*`

REM run with cmd /k $PWD/tools/release_windows.bat

setlocal EnableDelayedExpansion

set SDKS=C:\Program Files\Microsoft SDKs\Windows
set SDK7=%SDKS%\v7.0
set SDK71=%SDKS%\v7.1
set PYROOT=C:\
set DISTUTILS_USE_SDK=1

for %%p in (35, 34, 27) do (
  if "%%p"=="27" (
    set SDK=%SDK7%
    set cmd=build bdist_egg bdist_wheel --zmq=bundled
  ) else (
    set SDK=%SDK71%
    set cmd=build bdist_wheel --zmq=bundled
  )

  for %%b in (64, 32) do (
    if "%%b"=="64" (
      set SUFFIX=_64
      set ARCH=/x64
      set VCARCH=amd64
    ) else (
      set SUFFIX=
      set ARCH=/x86
      set VCARCH=
    )
    set PY=%PYROOT%\Python%%p!SUFFIX!\Python
    echo !PY! !SDK!
    !PY! -m ensurepip
    !PY! -m pip install --upgrade setuptools pip wheel
    if !errorlevel! neq 0 exit /b !errorlevel!

    if "%%p"=="35" (
      rem no SDK for 3.5, but force static-linking with DISTUTILS_USE_SDK=1 anyway
      rem to avoid missing MSVCP140.dll
      @call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" !VCARCH!
    ) else (
      @call "!SDK!\Bin\SetEnv.cmd" /release !ARCH!
      if !errorlevel! neq 0 exit /b !errorlevel!
    )
    @echo on
    !PY! setup.py !cmd!
    @echo off
    if !errorlevel! neq 0 exit !errorlevel!
  )
)
exit
