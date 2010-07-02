"""Plot latency data from messaging benchmarks.

To generate the data for each library, I started the server and then did
the following for each client::

    from xmlrpc_client import client
    for i in range(9):
        s = '0'*10**i
        print s
        %timeit client.echo(s)
"""

from matplotlib.pylab import *

rawdata = """# Data in milliseconds
Bytes	JSONRPC	PYRO	XMLRPC	pyzmq_copy	pyzmq_nocopy
1	2.15	0.186	2.07	0.111	0.136
10	2.49	0.187	1.87	0.115	0.137
100	2.5	0.189	1.9	0.126	0.138
1000	2.54	0.196	1.91	0.129	0.141
10000	2.91	0.271	2.77	0.204	0.197
100000	6.65	1.44	9.17	0.961	0.546
1000000	50.2	15.8	81.5	8.39	2.25
10000000	491	159	816	91.7	25.2
100000000	5010	1560	8300	893	248

"""
with open('latency.csv','w') as f:
    f.writelines(rawdata)

data = csv2rec('latency.csv',delimiter='\t')

loglog(data.bytes, data.xmlrpc*1000, label='XMLRPC')
loglog(data.bytes, data.jsonrpc*1000, label='JSONRPC')
loglog(data.bytes, data.pyro*1000, label='Pyro')
loglog(data.bytes, data.pyzmq_nocopy*1000, label='PyZMQ')
loglog(data.bytes, len(data.bytes)*[60], label='Ping')
legend(loc=2)
title('Latency')
xlabel('Number of bytes')
ylabel('Round trip latency ($\mu s$)')
grid(True)
show()
savefig('latency.png')

clf()

semilogx(data.bytes, 1000/data.xmlrpc, label='XMLRPC')
semilogx(data.bytes, 1000/data.jsonrpc, label='JSONRPC')
semilogx(data.bytes, 1000/data.pyro, label='Pyro')
semilogx(data.bytes, 1000/data.pyzmq_nocopy, label='PyZMQ')
legend(loc=1)
xlabel('Number of bytes')
ylabel('Message/s')
title('Message Throughput')
grid(True)
show()
savefig('msgs_sec.png')

clf()

loglog(data.bytes, 1000/data.xmlrpc, label='XMLRPC')
loglog(data.bytes, 1000/data.jsonrpc, label='JSONRPC')
loglog(data.bytes, 1000/data.pyro, label='Pyro')
loglog(data.bytes, 1000/data.pyzmq_nocopy, label='PyZMQ')
legend(loc=3)
xlabel('Number of bytes')
ylabel('Message/s')
title('Message Throughput')
grid(True)
show()
savefig('msgs_sec_log.png')

clf()

semilogx(data.bytes, data.pyro/data.pyzmq_nocopy, label="No-copy")
semilogx(data.bytes, data.pyro/data.pyzmq_copy, label="Copy")
xlabel('Number of bytes')
ylabel('Ratio throughputs')
title('PyZMQ Throughput/Pyro Throughput')
grid(True)
legend(loc=2)
show()
savefig('msgs_sec_ratio.png')
