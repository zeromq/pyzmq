# Enabling CURVE security

libzmq has a security mechanism called CURVE for encrypting and authenticating communication,
which is generally available in pyzmq wheel installs for reasonably supported versions with libzmq >=4.2.

```{seealso}
libzmq's [CURVE documentation](https://libzmq.readthedocs.io/en/latest/zmq_curve.html) for more details on how CURVE works.
```

## Quickstart

To start, you'll need to generate a "curve keypair" for your server:

```python
server_public, server_secret = zmq.curve_keypair()
```

**One** of your sockets, typically the one that binds, must be identified as the "curve server",
with the secret key above:

```python
listener.curve_server = True
listener.curve_secretkey = server_secret
```

and any clients must set the server's public key as `curve_serverkey`:

```python
connector.curve_serverkey = server_publickey
```

This is how clients _authenticate_ with the server.
Without this set to the right value, sockets won't be able to connect.
Anyone with access to `server_publickey` will be able to open a connection to your socket.

Clients must also set a public/secret key pair.
These only need to be a valid key pair, not any special values, and each client should have a different key pair:

```python
connector.curve_publickey, connector.curve_secretkey = zmq.curve_keypair()
```

At this point, your two sockets should be able to establish a secure connection:

```python
listener.bind(url)
connector.connect(url)
```

### Example

A full, working example of two sockets connected with CURVE security:

```{literalinclude} keygen.py
```

## Generating keys

The libzmq API [`zmq_curve_keypair`](https://libzmq.readthedocs.io/en/latest/zmq_curve_keypair.html) is available in pyzmq as {func}`zmq.curve_keypair`.
There is also an API [`zmq_curve_public`](https://libzmq.readthedocs.io/en/latest/zmq_curve_public.html) ({func}`zmq.curve_public`) to re-derive the public key, given only the secret key.
libzmq has a command-line utility `curve_keygen` for generating a key pair.
pyzmq 27.2 has an equivalent entrypoint:

```bash
python3 -m zmq.curve_keygen
```

```
== CURVE PUBLIC KEY ==
=Pk(ZaVEh@A-Iu?o&UzR8XAg@GSUI]G$c&kns...

== CURVE SECRET KEY ==
m+Vd2TC.}sJ4)*YS/n%=thlV*/:##iNXWwv}E...
```

You can also request more machine-friendly JSON output:

```bash
python3 -m zmq.curve_keygen --json
```

```json
{
 "public": "57TA6>1NU^x0fF6C.)bBSimuLoZmIkyaP3IHh...",
 "secret": ".{@vC[ir+cDtRBKlFc:sx8DGFtgwN}?@UT:>D..."
}
```

And even access the `zmq_curve_publickey` entrypoint to re-derive the public key, given an existing secret key:

```bash
python3 -m zmq.curve_keygen --json --secret "PLTZ/RHpF8C@QEPHT3fETV&0:uRVw0[b*A3pH..."
```

```json
{
 "public": "MFGz8UhD5oreRIxvQW[i*wmF)(Z-No&j-yWRPFu$",
 "secret": "PLTZ/RHpF8C@QEPHT3fETV&0:uRVw0[b*A3pH..."
}
```

zmq curve keys are always 32 z85-encoded bytes, which means they are 40 character ASCII strings.
You never have to deal with the z85 decoding, all libzmq APIs expect z85-encoded keys,
which means all zmq keys you have to deal with will be ASCII-safe strings,
suitable for working with as text.
