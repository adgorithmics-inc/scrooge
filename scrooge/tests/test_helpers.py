from scrooge import RedisScrooge
from scrooge.contrib.helpers import RedisSemaphore, lock_task_semaphore
from scrooge.exceptions import TaskLockedException
from scrooge.tests.base import BaseTestCase


class TestLockTaskSemaphore(BaseTestCase):
    def setUp(self):
        super(TestLockTaskSemaphore, self).setUp()
        self.semaphore = RedisSemaphore(self.scrooge, "lock_a", 2)
        self.scrooge.storage.conn.delete(self.semaphore.key)

    def tearDown(self):
        self.scrooge.storage.conn.delete(self.semaphore.key)
        super(TestLockTaskSemaphore, self).tearDown()

    def get_scrooge(self):
        return RedisScrooge()

    def test_redis_semaphore(self):
        s = self.semaphore
        aid1 = s.acquire()
        self.assertTrue(aid1 is not None)
        aid2 = s.acquire()
        self.assertTrue(aid2 is not None)  # We can acquire it twice.
        self.assertTrue(s.acquire() is None)  # Cannot acquire 3 times.
        self.assertEqual(s.release(aid2), 1)  # Release succeeded.
        self.assertEqual(s.release(aid2), 0)  # Already released.
        self.assertEqual(s.acquire(aid2), aid2)  # Re-acquired.
        self.assertEqual(s.acquire(aid2), aid2)  # No-op (still acquired).

        self.assertEqual(s.release(aid2), 1)  # Release succeeded.
        self.assertEqual(s.release(aid1), 1)  # Release succeeded.

        self.assertTrue(s.acquire() is not None)  # Acquire twice.
        self.assertTrue(s.acquire() is not None)
        self.assertTrue(s.acquire() is None)  # Cannot acquire 3 times.
        self.scrooge.storage.conn.delete(s.key)
