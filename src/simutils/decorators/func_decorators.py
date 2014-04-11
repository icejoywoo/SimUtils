#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-8

__author__ = 'wujiabin'
import re
import threading
import time


class Wrapper(object):
    """
    A lib uniform api wrapper
    """
    pass

func = Wrapper()


def invoked_once(func):
    """
    Decorate a method which just can be invoked only once.
    确保方法只会被调用一次
    """
    func.__called = False

    def wrapper(*args, **kargs):
        #print('func_name: %r, callled: %r,' % (func.__name__, func.__called), args, kargs)
        if func.__called:
            return None
        else:
            func.__called = True
            return func(*args, **kargs)
    return wrapper

func.invoked_once = invoked_once


# 还有其他实现, 参考: https://github.com/the5fire/Python-LRU-cache
class Memoize:
    """
    'Memoizes' a function, caching its return values for each input.
    If `expires` is specified, values are recalculated after `expires` seconds.
    If `background` is specified, values are recalculated in a separate thread.

    COPY FROM WEB.PY
        >>> calls = 0
        >>> def howmanytimeshaveibeencalled():
        ...     global calls
        ...     calls += 1
        ...     return calls
        >>> fastcalls = memoize(howmanytimeshaveibeencalled)
        >>> howmanytimeshaveibeencalled()
        1
        >>> howmanytimeshaveibeencalled()
        2
        >>> fastcalls()
        3
        >>> fastcalls()
        3
        >>> import time
        >>> fastcalls = memoize(howmanytimeshaveibeencalled, .1, background=False)
        >>> fastcalls()
        4
        >>> fastcalls()
        4
        >>> time.sleep(.2)
        >>> fastcalls()
        5
        >>> def slowfunc():
        ...     time.sleep(.1)
        ...     return howmanytimeshaveibeencalled()
        >>> fastcalls = memoize(slowfunc, .2, background=True)
        >>> fastcalls()
        6
        >>> timelimit(.05)(fastcalls)()
        6
        >>> time.sleep(.2)
        >>> timelimit(.05)(fastcalls)()
        6
        >>> timelimit(.05)(fastcalls)()
        6
        >>> time.sleep(.2)
        >>> timelimit(.05)(fastcalls)()
        7
        >>> fastcalls = memoize(slowfunc, None, background=True)
        >>> threading.Thread(target=fastcalls).start()
        >>> time.sleep(.01)
        >>> fastcalls()
        9
    """
    def __init__(self, func, expires=None, background=True):
        self.func = func
        self.cache = {}
        self.expires = expires
        self.background = background
        self.running = {}

    def __call__(self, *args, **keywords):
        key = (args, tuple(keywords.items()))
        if not self.running.get(key):
            self.running[key] = threading.Lock()

        def update(block=False):
            if self.running[key].acquire(block):
                try:
                    self.cache[key] = (self.func(*args, **keywords), time.time())
                finally:
                    self.running[key].release()

        if key not in self.cache:
            update(block=True)
        elif self.expires and (time.time() - self.cache[key][1]) > self.expires:
            if self.background:
                threading.Thread(target=update).start()
            else:
                update()
        return self.cache[key][0]

memoize = Memoize
func.ret_cached = Memoize

re_compile = memoize(re.compile)  # not thread-safe
re_compile.__doc__ = """
A cached version of re.compile from web.py.
"""

if __name__ == "__main__":
    @memoize
    def t(a):
        print "ttt"
        return a + 1

    print t(1)
    print t(2)
    print t(1)