"""
info about the bundled versions of libzmq

no longer any info other than version numbers
"""

import sys

bundled_libsodium_version = "1.0.19"
bundled_version = "4.3.5"


def main():
    """print version

    for easier consumption by non-python
    """
    if sys.argv[1:2] == ['libsodium']:
        v = bundled_libsodium_version
    else:
        v = bundled_version
    sys.stdout.write(v)


if __name__ == "__main__":
    main()
