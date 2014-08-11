#!/bin/env python
# ^_^ encoding: utf-8 ^_^
# @date: 2014/8/8
"""
worker_pool
简单的线程池, 提交任务即可, 会后台执行, 并将结果返回
示例见main部分
TODO
1. 清空status的时机, 删除已经返回的key, 否则内存要爆
"""

__author__ = 'wujiabin'

import threading
import Queue


class WorkerPoolError(Exception):
    pass


class TaskNotFinishedException(Exception):
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
                self.status[key]['status'] = 'running'
                self.status[key]['ret'] = call()
                self.status[key]['status'] = 'done'
            except:
                self.status[key]['status'] = 'error'
                pass
            self.queue.task_done()


class WorkerPool(object):
    """
    A simple method pool which can run in multi-thread and cache the result.
    Result is not a thread-safe dict, but some operations are atomic in CPython.
    http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm
    """

    def __init__(self, thread_num=5, cache_result=False):
        """
        :param thread_num: worker的数目
        :param cache_result: 是否cache方法返回的结果.
        :return: None
        """
        self.thread_num = thread_num
        self.queue = Queue.Queue()
        # 保存task运行的状态
        self.status = {}

        self.cache_result = cache_result

        self.workers = [Worker(self.queue, self.status) for i in xrange(self.thread_num)]
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

        def _func(*args, **kwargs):
            """
            function wrapper: make it as a function without args
            :param args: original method's args
            :param kwargs: original method's kwargs
            :return:
            """
            key = (func.__name__, args, tuple(kwargs.items()))
            # 如果可以返回缓存结果就返回缓存结果
            if self.cache_result:
                # cached status
                if key in self.status and self.status[key]['status'] == 'done':
                    return self.status[key]['ret']
            self.status.setdefault(key, {'status': 'ready'})
            self.queue.put((key, lambda: func(*args, **kwargs)))
            # wait for the status
            while self.status[key]['status'] != 'done':
                pass
            return self.status[key]['ret']
        return _func

    def add_task(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        :return:
        """

        class Task(object):

            def __init__(self, status, task_id):
                self.status = status
                self.task_id = task_id

            def get_status(self):
                return self.status['status']

            def get_ret(self):
                while self.get_status() != 'done':
                    pass
                return self.status['ret']

            def get_ret_nowait(self):
                if self.get_status() != 'done':
                    raise TaskNotFinishedException("Task is not finished yet. task_id -> {0}".format(self.task_id))
                else:
                    return self.status['ret']

        if self.cache_result:
            key = (func.__name__, args, tuple(kwargs.items()))
        else:
            import time
            key = (func.__name__, args, tuple(kwargs.items()), time.time())
        # 如果可以返回缓存结果就返回缓存结果
        if self.cache_result:
            # cached status
            if key in self.status and self.status[key]['status'] == 'done':
                return self.status[key]['ret']
        self.status[key] = {'status': 'ready'}
        self.queue.put((key, lambda: func(*args, **kwargs)))
        return Task(self.status[key], key)

    """ with-statement wrapper """
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()


if __name__ == "__main__":
    import thread
    # 1. with cache
    with WorkerPool(thread_num=5, cache_result=True) as p:
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

    # 2. add task without cache
    p = WorkerPool(thread_num=5)

    def bar(a, b, c):
        import time
        time.sleep(0.1)
        print 'bar>', thread.get_ident(), '>', a, b, c
        return a + b * c

    task = p.add_task(bar, i, i+2, c=3)
    try:
        print task.get_ret_nowait()
    except TaskNotFinishedException:
        pass
    print task.get_ret()

    tasks = []
    for i in xrange(100):
        tasks.append(p.add_task(bar, i, i+2, c=3))

    for task in tasks:
        print task.get_ret()
