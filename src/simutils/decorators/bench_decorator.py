#!/bin/env python
#^_^ encoding: utf-8 ^_^
# @date: 14-1-10

__author__ = 'wujiabin'

import collections
import Queue
import threading
import time

# 是否运行的标记
is_running = True


# replace: Record = collections.namedtuple('Record', 'time latency ret')
class Record(object):
    __slots__ = ('time', 'latency', 'ret')

    def __init__(self, time, latency, ret):
        self.time = time
        self.latency = latency
        self.ret = ret


class Benchmark(object):
    def __init__(self, worker, **kvargs):
        # 用queue做tickets来做速度控制
        self.tickets = Queue.Queue()
        self.kvargs = kvargs

        self.worker = worker
        self.worker_num = kvargs.get("worker_num", 10)

        self.total_reporter = []
        self.reporter = []
        self.all_threads = []

    def run(self):
        worker_threads = [threading.Thread(target=self.worker, args=(self, self.kvargs)) for _ in
                          xrange(self.worker_num)]
        [(t.setDaemon(True), t.start()) for t in worker_threads]
        self.all_threads += worker_threads

    def loop(self):
        self.run()
        # join会导致主线程hang住, 无法接受信号
        # [t.join() for t in self.all_threads]
        start = time.time()
        tickets_count = self.kvargs.get("max_qps", 2 ** 32)
        step = self.kvargs.get("step", 1)
        while is_running:
            if (time.time() - start) * 1000 < 1000 and tickets_count > 0:
                self.tickets.put(step)
                tickets_count -= step
            else:
                tickets_count = self.kvargs["max_qps"]
                if (time.time() - start) * 1000 < 1000:
                    time.sleep(1.0 - (time.time() - start))
                start = time.time()
                if self.reporter:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    latencies = [i.latency for i in self.reporter]
                    print "[%s] qps: %d\tmax_latency: %d\tmin_latency: %d\tavg_latency: %d" \
                          % (timestamp, len(self.reporter), max(latencies), min(latencies),
                             sum(latencies) / len(latencies))
                    self.total_reporter += self.reporter
                    self.reporter = []
            # print summary
        self.summary()

    def stop(self):
        for t in self.all_threads:
            t.kill_received = True
        global is_running
        is_running = False

    def summary(self):
        # summary
        latencies = [i.latency for i in self.total_reporter]
        print "operation count: %d\tavg_latency: %d" \
              % (len(latencies), sum(latencies) / len(latencies))


def worker(func):
    """
    @param func: decorator method's function
    @return: a benchmark worker
    """

    def __worker(bench, kvargs):
        while is_running:
            count = bench.tickets.get()
            for _ in xrange(count):
                start = time.time()
                ret = func(kvargs)
                latency = (time.time() - start) * 1000000  # ns
                bench.reporter.append(Record(start, latency, ret))
            bench.tickets.task_done()

    return __worker

if __name__ == "__main__":
    import os
    @worker
    def test_worker(kvargs):
        if kvargs["step"] == 1:
            return 0
        else:
            return -1


    @worker
    class worker_class(object):
        def __init__(self, kvargs):
            self.kvargs = kvargs

        def __call__(self, *args, **kwargs):
            if self.kvargs["step"] == 1:
                return 0
            else:
                return -1


    def closure():
        print "reading file..."
        lines = [l.rstrip() for l in file(os.path.abspath(__file__))]
        print "finished"

        @worker
        def _worker(kvargs):
            if lines[0] == 1:
                return 0
            else:
                return -1

        return _worker


    # worker_num = 1 时, 计算性能已经很不错了, 如果io比较多的情况下, 可以增加线程数
    # 因为GIL, 多线程无法使用多核
    config = {
        "worker_num": 1,
        "time": 20,
        "max_qps": 1000000,
        "step": 1,  # step 越小 qps控制得越好
    }

    from simutils.decorators.util_decorators import Timer
    # 简单测试
    with Timer(True):
        # b = Benchmark(test_worker, **config)
        # b = Benchmark(worker_class, **config)
        b = Benchmark(closure(), **config)
        b.loop()
