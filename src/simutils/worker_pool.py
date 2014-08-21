#!/bin/env python
# ^_^ encoding: utf-8 ^_^
# @date: 2014/8/8
"""
worker_pool
简单的线程池, 提交任务即可, 会后台执行, 并将结果返回
提供同步和异步两种方式, 同步方式没什么优势
"""

__author__ = 'wujiabin'

import threading
import Queue


class WorkerPoolError(Exception):
    pass


class TaskNotFinishedException(Exception):
    pass


class ResultNotReadyException(Exception):
    pass


class Worker(threading.Thread):
    """ A simple worker to get task from queue.
    """

    def __init__(self, queue, status):
        threading.Thread.__init__(self)
        self.queue = queue
        self.status = status
        self.running = True

    def cancel(self):
        self.running = False

    def run(self):
        while self.running:
            key, call = self.queue.get()
            try:
                status = self.status[key]
                status['status'] = 'running'
                status['ret'] = call()
                status['status'] = 'done'
            except:
                status['status'] = 'error'
                pass
            self.queue.task_done()


class WorkerPool(object):
    """
    A simple method pool which can run in multi-thread and cache the result.
    Result is not a thread-safe dict, but some operations are atomic in CPython.
    http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
    """

    def __init__(self, thread_num=5, cache_result=False, async=True):
        """
        :param thread_num: worker的数目
        :param max_size: status的大小, 超过可能会导致异常的
        :param cache_result: 是否cache方法返回的结果.
        :return: None
        """
        self.thread_num = thread_num
        self.queue = Queue.Queue()
        # 保存task运行的状态
        self.status = {}
        self.async = async

        self.cache_result = cache_result

        self.workers = [Worker(self.queue, self.status) for _ in xrange(self.thread_num)]
        self.is_join = False
        self.counter = 0

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

    def join(self):
        self.is_join = True
        self.queue.join()
        self.is_join = False
        return

    def run_with(self, func):
        """
        A function decorator, to let the method to run in parallel.

        :param func:
        :return:
        """
        if self.is_join:
            raise WorkerPoolError("WorkerPool has been joined and cannot add new worker")

        class FutureResult(object):

            def __init__(self, p_status, func_id):
                self._pool_status = p_status
                self._status = p_status[func_id]
                self._func_id = func_id

            def ready(self):
                result = self._status['status'] == 'done'
                if result:
                    self._status = self._pool_status.pop(self._func_id)
                return result

            def result(self):
                if self.ready():
                    return self._status['ret']
                else:
                    raise ResultNotReadyException("Result is *NOT* ready.")

        def _func(*args, **kwargs):
            """
            function wrapper: make it as a function without args
            :param args: original method's args
            :param kwargs: original method's kwargs
            :return:
            """
            if self.cache_result:
                key = (func.__name__, args, tuple(kwargs.items()))
            else:
                import time
                key = (func.__name__, args, tuple(kwargs.items()), time.time(), self.counter)
            self.counter += 1
            self.status.setdefault(key, {'status': 'ready'})
            self.queue.put((key, lambda: func(*args, **kwargs)))
            if self.async:
                return FutureResult(self.status, key)
            else:
                # block and wait for the status
                while self.status[key]['status'] != 'done':
                    pass
                return self.status.pop(key)['ret']
        return _func

    """ with-statement wrapper """
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()


if __name__ == "__main__":
    import thread
    # 同步池子, 没什么优势 async = False
    with WorkerPool(thread_num=5, async=False) as p:
        @p.run_with
        def foo(a):
            import time
            time.sleep(0.1)
            print 'foo>', thread.get_ident(), '>', a
            return a

        for i in xrange(10):
            print foo(i)

        # cached ret
        for i in xrange(10):
            print foo(i)

    # 异步池子
    with WorkerPool(thread_num=5, async=True) as p:
        @p.run_with
        def foo(a):
            import time
            time.sleep(0.1)
            print 'foo>', thread.get_ident(), '>', a
            return a

        for i in xrange(10):
            print foo(i)

        # cached ret
        for i in xrange(10):
            print foo(i)
