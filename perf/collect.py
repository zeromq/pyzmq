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
        yield lambda : toc - tic
    finally:
        toc = monotonic()


def compute_data_point(test, size, copy=True, poll=False, transport='ipc', t_min=1, t_max=3):
    url = URLs.get(transport)
    duration = 0
    count = 2
    results = []
    print('copy=%s, size=%s' % (copy, size))
    while duration < t_max:
        with timer() as get_duration:
            result = do_run(test, count=count, size=size, copy=copy, url=url, quiet=True)
        duration = get_duration()
        print('  %8i %.2g %.2g' % (count, result, duration))
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


def main():
    fname = 'data.pickle'
    import pandas as pd
    data = []
    transport = 'ipc'
    poll = False
    before = None
    if os.path.exists(fname):
        with open(fname, 'rb') as f:
            before = pickle.load(f)
    for size in np.logspace(2,4,9).astype(int):
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
            for result, count in compute_data_point('thr', size,
                    copy=copy, transport=transport, poll=poll):
                data.append(
                    (size, count, result, copy, poll, transport),
                )
                df = pd.DataFrame(data,
                    columns=['size', 'count', 'throughput', 'copy', 'poll', 'transport'])
                if before is not None:
                    df = pd.concat([before, df])
                df.to_pickle(fname)

if __name__ == '__main__':
    main()
