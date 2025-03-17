% PyZMQ ssh doc, by Min Ragan-Kelley, 2011

(ssh)=

# Tunneling PyZMQ Connections with SSH

```{versionadded} 2.1.9
```

You may want to connect ØMQ sockets across machines, or untrusted networks. One common way
to do this is to tunnel the connection via SSH. [IPython] introduced some tools for
tunneling ØMQ connections over ssh in simple cases. These functions have been brought into
pyzmq as {mod}`zmq.ssh.tunnel` under IPython's BSD license.

PyZMQ will use the shell ssh command via [pexpect] by default, but it also supports
using [paramiko] for tunnels, so it should work on Windows.

An SSH tunnel has five basic components:

- server : the SSH server through which the tunnel will be created
- remote ip : the IP of the remote machine *as seen from the server*
  (remote ip may be, but is not not generally the same machine as server).
- remote port : the port on the remote machine that you want to connect to.
- local ip : the interface on your local machine you want to use (default: 127.0.0.1)
- local port : the local port you want to forward to the remote port (default: high random)

So once you have established the tunnel, connections to `localip:localport` will actually
be connections to `remoteip:remoteport`.

In most cases, you have a zeromq url for a remote machine, but you need to tunnel the
connection through an ssh server. This is

So if you would use this command from the same LAN as the remote machine:

```python
sock.connect("tcp://10.0.1.2:5555")
```

to make the same connection from another machine that is outside the network, but you have
ssh access to a machine `server` on the same LAN, you would simply do:

```python
from zmq import ssh

ssh.tunnel_connection(sock, "tcp://10.0.1.2:5555", "server")
```

Note that `"server"` can actually be a fully specified `"user@server:port"` ssh url.
Since this really just launches a shell command, all your ssh configuration of usernames,
aliases, keys, etc. will be respected. If necessary, {func}`.tunnel_connection` does take
arguments for specific passwords, private keys (the ssh `-i` option), and non-default
choice of whether to use paramiko.

If you are on the same network as the machine, but it is only listening on localhost, you
can still connect by making the machine itself the server, and using loopback as the
remote ip:

```python
from zmq import ssh

ssh.tunnel_connection(sock, "tcp://127.0.0.1:5555", "10.0.1.2")
```

The {func}`.tunnel_connection` function is a simple utility that forwards a random
localhost port to the real destination, and connects a socket to the new local url,
rather than the remote one that wouldn't actually work.

```{seealso}
A short discussion of ssh tunnels: <https://www.revsys.com/writings/quicktips/ssh-tunnel.html>
```

[ipython]: https://ipython.org
[paramiko]: https://www.lag.net/paramiko/
[pexpect]: https://pexpect.readthedocs.io
