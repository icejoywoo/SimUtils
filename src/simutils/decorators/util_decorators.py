#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-4-9

__author__ = 'wujiabin'

import time
import sys


class Timer(object):
    """
    simple timer 可以在退出的时候打报告什么的
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

import threading
import Queue


class WorkerPoolError(Exception):
    pass


class Worker(threading.Thread):

    def __init__(self, queue, result):
        threading.Thread.__init__(self)
        self.queue = queue
        self.result = result
        self.running = True

    def cancel(self):
        self.running = False

    def run(self):
        while self.running:
            key, call = self.queue.get()
            try:
                self.result[key] = call()
            except:
                pass
            self.queue.task_done()


class WorkerPool(object):
    """
    A simple method pool which can run in multi-thread and cache the result.
    Result is not a thread-safe dict, but some operations are atomic in CPython.
    http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
    """

    def __init__(self, threadnum=5):
        self.threadnum = threadnum
        self.queue = Queue.Queue()
        # 保存结果, 并且可以保持函数的以前运行结果
        self.result = {}

        self.workers = [Worker(self.queue, self.result) for i in xrange(self.threadnum)]
        self.is_join = False

        # start workers
        for w in self.workers:
            w.setDaemon(True)
            w.start()

    def __del__(self):
        try:
            for w in self.workers:
                w.cancel()
        except:
            pass

    def __call__(self, func):
        if not self.is_join:
            self.queue.put(func)
        else:
            raise WorkerPoolError("WorkerPool has been joined and cannot add new worker")

    def join(self):
        self.is_join = True
        self.queue.join()
        self.is_join = False
        return

    def run_with(self, func):
        def _func(*args, **kwargs):
            key = (func.__name__, args, tuple(kwargs.items()))
            # cached result
            if key in self.result:
                return self.result[key]
            self.result.setdefault(key, None)
            self.queue.put((key, lambda: func(*args, **kwargs)))
            # wait for the result
            while self.result[key] is None:
                pass
            return self.result[key]
        return _func

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()

if __name__ == "__main__":
    import thread
    with WorkerPool(5) as p:
        @p.run_with
        def foo(a):
            import time
            time.sleep(a)
            print 'foo>', thread.get_ident(), '>', a
            return a

        for i in xrange(10):
            print foo(i)

        # cached ret
        print foo(1)