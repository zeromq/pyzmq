from timeit import default_timer as timer

def benchmark(f, size, reps):
    msg = size*'0'
    t1 = timer()
    for i in range(reps):
        msg2 = f(msg)
        assert msg == msg2
    t2 = timer()
    diff = (t2-t1)
    latency = diff/reps
    return latency*1000000

kB = [1000*2**n for n in range(10)]
MB = [1000000*2**n for n in range(8)]
sizes = [1] + kB + MB

def benchmark_set(f, sizes, reps):
    latencies = []
    for size, rep in zip(sizes, reps):
        print "Running benchmark with %r reps of %r bytes" % (rep, size)
        lat = benchmark(f, size, rep)
        latencies.append(lat)
    return sizes, latencies

