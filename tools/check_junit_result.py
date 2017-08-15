from __future__ import print_function

import os
import argparse
from xml.etree import cElementTree


def main(filename):
    tree = cElementTree.parse(filename)
    root = tree.getroot()
    attributes = root.attrib
    errors = int(attributes.get('errors', '0'))
    failures = int(attributes.get('failures', '0'))
    tests = int(attributes.get('tests', '0'))
    if tests == 0:
        print('No tests run')
        exit(1)
    elif errors + failures > 0:
        print('Test runs failed')
        for testcase in root:
            for item in testcase:
                if item.tag == 'failure' or item.tag == 'error':
                    print('=' * 50)
                    print(item.text)
                    print('=' * 50)
        exit(1)
    else:
        print('All tests {} passed'.format(tests))
        for testcase in root:
            attributes = testcase.attrib
            print("{name}{classname}".format(**attributes))
        exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename",
        help="The filename of the junit xml result file")
    args = parser.parse_args()
    main(args.filename)
