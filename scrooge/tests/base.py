import contextlib
import logging
import os
import unittest

from scrooge.api import MemoryScrooge
from scrooge.consumer import Consumer
from scrooge.exceptions import TaskException


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger("scrooge")
logger.addHandler(NullHandler())

TRAVIS = bool(os.environ.get("SCROOGE_TRAVIS"))


class BaseTestCase(unittest.TestCase):
    consumer_class = Consumer

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.scrooge = self.get_scrooge()

    def get_scrooge(self):
        return MemoryScrooge(utc=False)

    def execute_next(self, timestamp=None):
        task = self.scrooge.dequeue()
        self.assertTrue(task is not None)
        return self.scrooge.execute(task, timestamp=timestamp)

    def trap_exception(self, fn, exc_type=TaskException):
        try:
            fn()
        except exc_type as exc_val:
            return exc_val
        raise AssertionError("trap_exception() failed to catch %s" % exc_type)

    def consumer(self, **params):
        params.setdefault("initial_delay", 0.001)
        params.setdefault("max_delay", 0.001)
        params.setdefault("workers", 2)
        params.setdefault("check_worker_health", False)
        return self.consumer_class(self.scrooge, **params)

    @contextlib.contextmanager
    def consumer_context(self, **kwargs):
        consumer = self.consumer(**kwargs)
        consumer.start()
        try:
            yield
        finally:
            consumer.stop(graceful=True)
