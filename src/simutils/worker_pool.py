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

from simutils import utils


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


class FutureResult(object):

    def __init__(self, p_status, func_id, worker_pool):
        self._pool_status = p_status
        self._status = p_status[func_id]
        self._func_id = func_id
        self.worker_pool = worker_pool
        self._is_finished = False

    def ready(self):
        result = self._status['status'] == 'done'
        if result:
            self._status = self._pool_status.pop(self._func_id)
            self.worker_pool._update_cache(self._func_id, self._status['ret'])
            self._is_finished = True
        return result

    def result(self):
        if self._is_finished:
            return self._status['ret']
        else:
            raise ResultNotReadyException("Result is *NOT* ready.")


class WorkerPool(object):
    """
    A simple method pool which can run in multi-thread and cache the result.
    Result is not a thread-safe dict, but some operations are atomic in CPython.
    http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
    """

    def __init__(self, thread_num=5, cache_result=False, cache_size=100, async=True):
        """
        :param thread_num: worker的数目
        :param cache_size: 指定cache的大小
        :param cache_result: 是否cache方法返回的结果.
        :param async: 是同步返回还是异步返回, 默认异步, 同步没有任何优势, 异步才有优势
        :return: None
        """
        self.thread_num = thread_num
        self.queue = Queue.Queue()
        # 保存task运行的状态
        self.status = {}
        self.async = async

        # 是否缓存结果, 缓存一定量的结果, 防止占用过多内存
        self.cache_result = cache_result
        if self.cache_result:
            self.cache = utils.LimitedSizeDict(size_limit=cache_size)

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

    def _update_cache(self, func_id, func_ret):
        if self.cache_result:
            self.cache[func_id] = func_ret

    def _get_cache(self, func_id):
        return self.cache.get(func_id, None)

    def run_with(self, func):
        """
        A function decorator, to let the method to run in parallel.

        :param func:
        :return:
        """
        if self.is_join:
            raise WorkerPoolError("WorkerPool has been joined and cannot add new worker")

        def _func(*args, **kwargs):
            """
            function wrapper: make it as a function without args
            :param args: original method's args
            :param kwargs: original method's kwargs
            :return:
            """
            try:
                if self.cache_result:
                    # 相同参数的调用, 会出现相同的func_id, 这样才能缓存结果
                    func_id = (func.__name__, args, tuple(kwargs.items()))
                    cache_ret = self._get_cache(func_id)
                    if cache_ret:
                        return cache_ret
                else:
                    import time
                    # 引入时间和counter, 不希望func_id出现重复
                    func_id = (func.__name__, args, tuple(kwargs.items()), time.time(), self.counter)

                self.status.setdefault(func_id, {'status': 'ready'})
            except TypeError as e:
                # TypeError: unhashable type args或kwargs可能存在可变类型, 会出现这个错误
                import time
                func_id = (func.__name__, time.time(), self.counter)
                self.cache_result = False
                self.status.setdefault(func_id, {'status': 'ready'})

            self.counter += 1
            self.queue.put((func_id, lambda: func(*args, **kwargs)))
            if self.async:
                return FutureResult(self.status, func_id, self)
            else:
                # block and wait for the status
                while self.status[func_id]['status'] != 'done':
                    pass
                self._update_cache(func_id, self.status[func_id]['ret'])
                return self.status.pop(func_id)['ret']
        return _func

    """ with-statement wrapper """
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()


if __name__ == "__main__":
    import itertools
    import thread
    # 同步池子, 没什么优势 async = False
    with WorkerPool(thread_num=5, async=False, cache_result=True, cache_size=10) as p:
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
    with WorkerPool(thread_num=5, async=True, cache_result=True,) as p:
        @p.run_with
        def foo(a):
            import time
            time.sleep(0.1)
            print 'foo>', thread.get_ident(), '>', a
            return a

        results = [foo([1, 2, 3]) for i in xrange(100)]

        while results:
            for index, result in enumerate(results):
                if result.ready():
                    print result.result()
                    results.remove(result)
