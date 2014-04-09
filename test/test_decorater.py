#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-8

__author__ = 'wujiabin'

from simutils import func


@func.lru_cached_ret(3, 1)
def f(x):
    print "Calling f(" + str(x) + ")"
    return x

# max_size test
print f(1)
print f(2)
print f(3)
print f(4)
print f(1)

# lru test
import time
time.sleep(2)
print f(1)