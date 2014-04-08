#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-8

__author__ = 'wujiabin'


def limited_once(func):
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



