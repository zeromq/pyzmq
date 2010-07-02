import Pyro.core

class Echo(Pyro.core.ObjBase):
        def __init__(self):
                Pyro.core.ObjBase.__init__(self)
        def echo(self, x):
                return x

Pyro.core.initServer()
daemon=Pyro.core.Daemon()
uri=daemon.connect(Echo(),"echo")

daemon.requestLoop()
    