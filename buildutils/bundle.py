"""
info about the bundled versions of libzmq

no longer any info other than version numbers
"""

import sys
from pathlib import Path
from urllib.request import urlretrieve

buildutils = Path(__file__).parent
repo_root = buildutils.parent.resolve()
licenses = repo_root / "licenses"

bundled_libsodium_version = "1.0.19"
bundled_version = "4.3.5"


def report_version(library="libzmq"):
    """Report the bundled version of the dependency"""
    if library == 'libsodium':
        v = bundled_libsodium_version
    else:
        v = bundled_version
    sys.stdout.write(v)


def fetch_licenses():
    """Download license files for bundled dependencies"""
    licenses.mkdir(exist_ok=True)
    libsodium_license_url = f"https://raw.githubusercontent.com/jedisct1/libsodium/{bundled_libsodium_version}/LICENSE"
    libzmq_license_url = (
        f"https://raw.githubusercontent.com/zeromq/libzmq/v{bundled_version}/LICENSE"
    )
    libzmq_license_file = licenses / "LICENSE.zeromq.txt"
    libsodium_license_file = licenses / "LICENSE.libsodium.txt"
    for dest, url in [
        (libzmq_license_file, libzmq_license_url),
        (libsodium_license_file, libsodium_license_url),
    ]:
        print(f"Downloading {url} -> {dest}")
        urlretrieve(url, dest)


def main():
    """print version

    for easier consumption by non-python
    """
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = "libzmq"

    if cmd in {"libzmq", "libsodium"}:
        report_version(cmd)
    elif cmd == "licenses":
        fetch_licenses()
    else:
        sys.exit(f"Unrecognized command: {cmd!r}")


if __name__ == "__main__":
    main()
