from collections.abc import Iterable


class Address(Iterable):
    def __init__(self, address, **kwargs):
        self._address = address

    def __str__(self):
        return self._address

    def __repr__(self):
        return '{}("{}")'.format(type(self).__name__, self._address)

    def __iter__(self):
        return iter((self._address,))


class TCPAddress(Address):
    def __init__(self, address, *, tcp_port=None, **kwargs):
        super().__init__(address, **kwargs)

        if address.endswith(']'):
            interface_port = (address,)
        else:
            interface_port = address.rsplit(':', maxsplit=1)

        self.interface = interface_port[0]
        self.port = interface_port[1] if len(interface_port) > 1 else tcp_port

        if self.port == '*':
            self.port = 0

        self.port = int(self.port) if self.port is not None else None

    @property
    def host(self):
        return self.interface

    @host.setter
    def host(self, value):
        self.interface = value

    def __iter__(self):
        return iter((self.interface, self.port))


class PGMAddress(Address):
    def __init__(self, address, **kwargs):
        super().__init__(address, **kwargs)

        if address.endswith(']'):
            interfacemulticast_port = (address,)
        else:
            interfacemulticast_port = address.rsplit(':', maxsplit=1)

        interface_multicast = interfacemulticast_port[0].split(';', maxsplit=1)

        self.interface = interface_multicast[0]
        self.multicast = interface_multicast[1]
        self.port = interfacemulticast_port[1] if len(interfacemulticast_port) > 1 else None
        self.port = int(self.port) if self.port is not None else None

    def __iter__(self):
        return iter((self.interface, self.multicast, self.port))


class VMCIAddress(TCPAddress):
    def __init__(self, address, *, vmci_port=None, **kwargs):
        super().__init__(address, tcp_port=vmci_port, **kwargs)

        if address.endswith('*'):
            self.port = -1


class Endpoint(Iterable):
    ADDRESS_MAP = {
        'tcp': TCPAddress,
        'inproc': Address,
        'ipc': Address,
        'pgm': PGMAddress,
        'epgm': PGMAddress,
        'tipc': None,
        'udp': TCPAddress,
        'vmci': VMCIAddress
    }

    def __init__(self, endpoint, *, scheme=None, **kwargs):
        scheme_address = endpoint.split('://', maxsplit=1)

        self.scheme = scheme_address[0] if len(scheme_address) > 1 else scheme

        if not self.scheme:
            raise ValueError("scheme must be specified")

        self.address = self.ADDRESS_MAP.get(self.scheme, Address)(scheme_address[-1], **kwargs)

    def __str__(self):
        return '{}://{}'.format(self.scheme, self.address)

    def __repr__(self):
        return 'Endpoint("{}")'.format(str(self))

    def __iter__(self):
        return iter((self.scheme, *self.address))
