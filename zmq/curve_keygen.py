"""
Generate a zmq curve keypair.

Generates a 'public' and a 'secret' key.
Add `--json` to output as a JSON dictionary.
Add `--secret SECRET` to derive public key from an existing secret key.

CURVE keys are always z85-encoded (ASCII safe).
"""

import argparse
import json
import sys

import zmq


def _main() -> None:
    parser = argparse.ArgumentParser(
        prog="python3 -m zmq.curve_keygen",
        description=__doc__,
    )
    parser.add_argument("--json", action="store_true", help="output keys as JSON dict")
    parser.add_argument(
        "--secret", type=str, help="specify secret key to derive a public key"
    )
    opts = parser.parse_args()
    if opts.secret:
        secret = opts.secret
        public = zmq.curve_public(secret.encode()).decode()
    else:
        public_b, secret_b = zmq.curve_keypair()
        public = public_b.decode()
        secret = secret_b.decode()
    if opts.json:
        json.dump(
            {
                "public": public,
                "secret": secret,
            },
            sys.stdout,
            indent=1,
            sort_keys=True,
        )
        sys.stdout.write("\n")
    else:
        # stdout, match libzmq curve_keygen format
        # without the big disclaimer
        print("== CURVE PUBLIC KEY ==")
        print(public)
        print()
        print("== CURVE SECRET KEY ==")
        print(secret)


if __name__ == "__main__":
    _main()
