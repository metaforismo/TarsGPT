"""Heartbeat scheduler: one background thread runs delayed and periodic jobs.

Skills use this for timers/reminders; the app uses it for battery watchdogs
and idle behaviors. Jobs run in worker threads so a slow job never blocks
the heartbeat.
"""
import heapq
import itertools
import logging
import threading
import time

log = logging.getLogger("tars.scheduler")


class Scheduler:
    def __init__(self):
        self._heap = []  # (when, seq, fn, interval)
        self._seq = itertools.count()
        self._cv = threading.Condition()
        self._running = False

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True, name="tars-heartbeat").start()

    def stop(self):
        with self._cv:
            self._running = False
            self._cv.notify()

    def schedule_in(self, delay_s: float, fn, *, interval_s: float | None = None) -> int:
        """Run fn after delay_s seconds; repeat every interval_s if given.
        Returns a job id usable with cancel()."""
        job_id = next(self._seq)
        with self._cv:
            heapq.heappush(self._heap, [time.monotonic() + delay_s, job_id, fn, interval_s])
            self._cv.notify()
        return job_id

    def every(self, interval_s: float, fn) -> int:
        return self.schedule_in(interval_s, fn, interval_s=interval_s)

    def cancel(self, job_id: int):
        with self._cv:
            for job in self._heap:
                if job[1] == job_id:
                    job[2] = None  # tombstone; skipped when it pops
                    return

    def _loop(self):
        while True:
            with self._cv:
                if not self._running:
                    return
                if not self._heap:
                    self._cv.wait()
                    continue
                when, job_id, fn, interval = self._heap[0]
                delay = when - time.monotonic()
                if delay > 0:
                    self._cv.wait(timeout=delay)
                    continue
                heapq.heappop(self._heap)
                if fn is not None and interval:
                    heapq.heappush(self._heap, [time.monotonic() + interval, job_id, fn, interval])
            if fn is not None:
                threading.Thread(target=self._run_job, args=(fn,), daemon=True).start()

    @staticmethod
    def _run_job(fn):
        try:
            fn()
        except Exception:
            log.exception("scheduled job failed")
