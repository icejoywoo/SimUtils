#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-8

__author__ = 'wujiabin'

from simutils.decorators import func


@func.ret_cached
def f(x):
    print "Calling f(" + str(x) + ")"
    return x

# max_size test
print f(1)
print f(2)
print f(3)
print f(4)
print f(1)
