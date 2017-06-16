"""
Collect data points for copy/no-copy crossover

Zero-copy has a finite overhead in pyzmq,
which is not worth paying for small messages.
"""

# Copyright (c) PyZMQ Developers.
# Distributed under the terms of the Modified BSD License.

import argparse
from contextlib import contextmanager
import os
import sys
import pickle
try:
    from time import monotonic
except ImportError:
    from time import time as monotonic

import numpy as np

from perf import do_run

URLs = {
    'tcp': 'tcp://127.0.0.1:5555',
    'ipc': 'ipc:///tmp/pyzmq-perf',
}

@contextmanager
def timer():
    tic = monotonic()
    toc = None
    try:
        yield lambda : toc - tic
    finally:
        toc = monotonic()


def compute_data_point(test, size, copy=True, poll=False, transport='ipc', t_min=1, t_max=3):
    url = URLs.get(transport)
    duration = 0
    count = 2
    results = []
    print('copy=%s, size=%s' % (copy, size))
    print('count result dt')
    while duration < t_max:
        with timer() as get_duration:
            result = do_run(test, count=count, size=size, copy=copy, url=url, quiet=True)
        duration = get_duration()
        print('  %8i %4i %5.02g' % (count, result, duration))
        if duration >= t_min:
            # within our window, record result
            results.append((result, count))
        if 10 * duration < t_min:
            # 10x if we are below 10% of t_min
            count *= 10
        elif duration < t_max:
            # 2x if we are getting close
            count *= 2
    return results

full_names = {
    'lat': 'latency',
    'thr': 'throughput',
}

def main():
    parser = argparse.ArgumentParser(description='Run a zmq performance test')
    parser.add_argument(dest='test', nargs='?', type=str, default='lat', choices=['lat', 'thr'],
                       help='which test to run')
    args = parser.parse_args()

    test = args.test
    full_name = full_names[test]
    print("Running %s test" % full_name)
    fname = test + '.pickle'
    import pandas as pd
    data = []
    transport = 'ipc'
    poll = False
    before = None
    if os.path.exists(fname):
        with open(fname, 'rb') as f:
            before = pickle.load(f)
    
    if test == 'lat':
        nmin = 3
        nmax = 7
        npoints = 9
        t_min = 0.4
        t_max = 3
    else:
        nmin = 2
        nmax = 4
        npoints = 9
        t_min = 1
        t_max = 3
    for size in np.logspace(nmin, nmax, npoints).astype(int):
        for copy in (True, False):
            if before is not None:
                matching = before[
                    (before['size'] > (0.8 * size)) & \
                    (before['size'] < (1.2 * size)) & \
                    (before['copy'] == copy) & \
                    (before['transport'] == transport) & \
                    (before['poll'] == poll)
                ]
                if len(matching):
                    print("Already have", matching)
                    continue
            for result, count in compute_data_point(test, size,
                    copy=copy, transport=transport, poll=poll, t_min=t_min, t_max=t_max):
                data.append(
                    (size, count, result, copy, poll, transport),
                )
                df = pd.DataFrame(data,
                    columns=['size', 'count', full_name, 'copy', 'poll', 'transport'])
                if before is not None:
                    df = pd.concat([before, df])
                df.to_pickle(fname)

if __name__ == '__main__':
    main()
