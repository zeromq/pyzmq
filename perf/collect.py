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
        yield lambda: toc - tic
    finally:
        toc = monotonic()


def compute_data_point(
    test, size, copy=True, poll=False, transport='ipc', t_min=1, t_max=3
):
    url = URLs.get(transport)
    duration = 0
    count = 2
    results = []
    print('copy=%s, size=%s' % (copy, size))
    print('%8s %5s %7s' % ('count', 'dt', 'result'))
    while duration < t_max:
        with timer() as get_duration:
            result = do_run(
                test, count=count, size=size, copy=copy, url=url, quiet=True
            )
        if not isinstance(result, tuple):
            result = (result,)
        duration = get_duration()
        fmt = '%8i %5.02g {}'.format('%7i ' * len(result))
        print(fmt % ((count, duration) + result))
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

result_columns = {
    'lat': ['latency'],
    'thr': ['sends', 'throughput'],
}


def main():
    parser = argparse.ArgumentParser(description='Run a zmq performance test')
    parser.add_argument(
        dest='test',
        nargs='?',
        type=str,
        default='lat',
        choices=['lat', 'thr'],
        help='which test to run',
    )
    parser.add_argument(
        '--points',
        type=int,
        default=3,
        help='how many data points to collect per interval',
    )
    parser.add_argument(
        '--max', type=int, default=0, help='maximum msg size (log10, so 3=1000)'
    )
    parser.add_argument(
        '--min', type=int, default=0, help='minimum msg size (log10, so 3=1000)'
    )
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
        nmin = args.min or 2
        nmax = args.max or 7
        t_min = 0.4
        t_max = 3
    else:
        nmin = args.min or 2
        nmax = args.max or 6
        t_min = 1
        t_max = 3
    npoints = args.points * (nmax - nmin) + 1
    sizes = np.logspace(nmin, nmax, npoints).astype(int)
    print("Computing %s datapoints: size=%s" % (len(sizes), list(sizes)))
    for size in np.logspace(nmin, nmax, npoints).astype(int):
        for copy in (True, False):
            if before is not None:
                matching = before[
                    (before['size'] > (0.8 * size))
                    & (before['size'] < (1.2 * size))
                    & (before['copy'] == copy)
                    & (before['transport'] == transport)
                    & (before['poll'] == poll)
                ]
                if len(matching):
                    print("Already have", matching)
                    continue
            for result, count in compute_data_point(
                test,
                size,
                copy=copy,
                transport=transport,
                poll=poll,
                t_min=t_min,
                t_max=t_max,
            ):

                data.append(
                    (size, count, copy, poll, transport) + result,
                )
                df = pd.DataFrame(
                    data,
                    columns=['size', 'count', 'copy', 'poll', 'transport']
                    + result_columns[test],
                )
                if before is not None:
                    df = pd.concat([before, df])
                df.to_pickle(fname)


if __name__ == '__main__':
    main()
