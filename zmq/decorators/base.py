from copy import copy
from functools import wraps

from zmq.utils.strtypes import basestring


class ZDecoratorBase(object):
    '''
    The mini decorator factory
    '''

    def __init__(self, target):
        self._target = target

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
        kwname, dec_args, dec_kwargs = self.pop_kwname(*dec_args, **dec_kwargs)

        def decorator(func):
            @wraps(func)
            def wrapper(*wrap_args, **wrap_kwargs):
                this = copy(self)
                this.target = this._target
                this.dec_args = dec_args
                this.dec_kwargs = dec_kwargs.copy()
                this.wrap_args = wrap_args
                this.wrap_kwargs = wrap_kwargs.copy()
                extra_arg = tuple()

                this.hook('preinit')

                try:
                    with this.target(*this.dec_args, **this.dec_kwargs) as obj:
                        this.hook('postinit')

                        if kwname and kwname not in wrap_kwargs:
                            wrap_kwargs[kwname] = obj
                        elif kwname and kwname in wrap_kwargs:
                            raise TypeError(
                                "{0}() got multiple values for"
                                " argument '{1}'".format(
                                    func.__name__, kwname))
                        else:
                            extra_arg = (obj,)

                        this.hook('preexec')
                        ret = func(*(wrap_args + extra_arg), **wrap_kwargs)
                        this.hook('postexec')
                        return ret
                except:
                    raise  # re-raise the exception
                finally:
                    this.hook('cleanup')

            return wrapper

        return decorator

    def hook(self, func):
        getattr(self, 'hook_{0}'.format(func), self.nop)()

    @staticmethod
    def nop(*args, **kwargs):
        pass  # and save the world silently

    def pop_kwname(self, *args, **kwargs):
        kwname = None

        if isinstance(kwargs.get('name'), basestring):
            kwname = kwargs.pop('name')
        elif len(args) >= 1 and isinstance(args[0], basestring):
            kwname = args[0]
            args = args[1:]

        return kwname, args, kwargs
