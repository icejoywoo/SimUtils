#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-8

__author__ = 'wujiabin'

from .. import thirdparty

@thirdparty.lru_cache_function
def f(x):
   print "Calling f(" + str(x) + ")"
   return x

print f(1)
print f(2)
print f(2)
