from functools import wraps

from zmq.utils.strtypes import basestring


class ZDecoratorBase(object):
    '''
    The mini decorator factory
    '''

    def __init__(self, target):
        self.target = target

    def __call__(self, *dec_args, **dec_kwargs):
        '''
        The main logic of decorator

        Here is how those arguments works::

            @out_decorator(*dec_args, *dec_kwargs)
            def func(*wrap_args, **wrap_kwargs):
                ...

        And in the ``wrapper``, we simply create ``self.target`` instance via
        ``with``::

            with self.target(*dec_args, **dec_kwargs) as obj:
                ...

        Hooks
            We also have hook functions for us to provide more custom logic.
            Just inherit this class and define the following function.
            - ``self.preinit``
            - ``self.postinit``
            - ``self.preexec``
            - ``self.postexec``
            - ``self.cleanup``
        '''
        self.kwname = None
        self.dec_args = dec_args
        self.dec_kwargs = dec_kwargs

        self.pop_kwname()

        def decorator(func):
            @wraps(func)
            def wrapper(*wrap_args, **wrap_kwargs):
                self.wrap_args = wrap_args  # read-only
                self.wrap_kwargs = wrap_kwargs.copy()  # read-only
                extra_arg = tuple()

                self.hook('preinit')

                try:
                    with self.target(*self.dec_args, **self.dec_kwargs) as obj:
                        self.hook('postinit')

                        if self.kwname and self.kwname not in wrap_kwargs:
                            wrap_kwargs[self.kwname] = obj
                        elif self.kwname and self.kwname in wrap_kwargs:
                            raise TypeError(
                                "{0}() got multiple values for"
                                " argument '{1}'".format(
                                    func.__name__, self.kwname))
                        else:
                            extra_arg = (obj,)

                        self.hook('preexec')
                        ret = func(*(wrap_args + extra_arg), **wrap_kwargs)
                        self.hook('postexec')
                        return ret
                except:
                    raise  # re-raise the exception
                finally:
                    self.hook('cleanup')

            return wrapper

        return decorator

    def hook(self, func):
        getattr(self, 'hook_{0}'.format(func), self.nop)()

    @staticmethod
    def nop(*args, **kwargs):
        pass  # and save the world silently

    def pop_kwname(self):
        if isinstance(self.dec_kwargs.get('name'), basestring):
            self.kwname = self.dec_kwargs.pop('name')
        elif (len(self.dec_args) >= 1 and
              isinstance(self.dec_args[0], basestring)):
            self.kwname = self.dec_args[0]
            self.dec_args = self.dec_args[1:]
