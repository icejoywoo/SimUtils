#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-9

__author__ = 'wujiabin'

import time
import sys


class Timer(object):
    """
    timer 可以在退出的时候打报告什么的
    """
    def __init__(self, verbose=False, fd=sys.stdout):
        self.verbose = verbose
        self.start = 0
        self.elapsed_ms = 0
        self._fd = fd

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.time() - self.start) * 1000
        if self.verbose:
            print >> self._fd, 'elapsed time: %f ms' % self.elapsed_ms
