import datetime

from scrooge.api import MemoryScrooge, crontab
from scrooge.exceptions import TaskException
from scrooge.tests.base import BaseTestCase


class TestPriority(BaseTestCase):
    def setUp(self):
        super(TestPriority, self).setUp()

        self.state = []

        def task(n):
            self.state.append(n)
            return n

        self.task_1 = self.scrooge.task(priority=1, name="task_1")(task)
        self.task_2 = self.scrooge.task(priority=2, name="task_2")(task)
        self.task_0 = self.scrooge.task(name="task_0")(task)

    def tearDown(self):
        super(TestPriority, self).tearDown()
        self.task_1 = self.task_2 = self.task_0 = None

    def test_priority_simple(self):
        self.task_0(0)
        self.task_1(10)
        self.task_2(100)

        self.task_0(2)
        self.task_1(12)
        self.task_2(120)
        self.assertEqual(len(self.scrooge), 6)

        # First the task_2 invocations, then the task_1, then the task_0.
        results = [100, 120, 10, 12, 0, 2]
        for result in results:
            self.assertEqual(self.execute_next(), result)

        self.assertEqual(len(self.scrooge), 0)
        self.assertEqual(self.state, results)

    def test_priority_override(self):
        r0_0 = self.task_0(0)
        r1_0 = self.task_1(10)
        r2_0 = self.task_2(100)

        r0_1 = self.task_0(1, priority=2)
        r1_1 = self.task_1(11, priority=0)
        r2_1 = self.task_2(110, priority=1)

        r0_2 = self.task_0(2, priority=1)
        r1_2 = self.task_1(12, priority=2)
        r2_2 = self.task_2(120, priority=0)

        results = [100, 1, 12, 10, 110, 2, 0, 11, 120]
        for result in results:
            self.assertEqual(self.execute_next(), result)

        self.assertEqual(len(self.scrooge), 0)
        self.assertEqual(self.state, results)

        r0_3 = self.task_0(3)
        r1_3 = self.task_1(13)
        r2_3 = self.task_2(130)
        rx = self.task_0(9, priority=9)
        results.extend((9, 130, 13, 3))
        for result in results[-4:]:
            self.assertEqual(self.execute_next(), result)

        self.assertEqual(len(self.scrooge), 0)
        self.assertEqual(self.state, results)

    def test_schedule_priority(self):
        eta = datetime.datetime.now() + datetime.timedelta(seconds=60)
        r0_0 = self.task_0.schedule((0,), eta=eta)
        r1_0 = self.task_1.schedule((10,), eta=eta)
        r2_0 = self.task_2.schedule((100,), eta=eta)

        r0_1 = self.task_0.schedule((1,), eta=eta, priority=2)
        r1_1 = self.task_1.schedule((11,), eta=eta, priority=0)
        r2_1 = self.task_2.schedule((110,), eta=eta, priority=1)

        expected = {
            r0_0.id: None,
            r1_0.id: 1,
            r2_0.id: 2,
            r0_1.id: 2,
            r1_1.id: 0,
            r2_1.id: 1,
        }

        for _ in range(6):
            self.assertTrue(self.execute_next() is None)

        # Priorities are preserved when added to the schedule.
        priorities = dict((t.id, t.priority) for t in self.scrooge.scheduled())
        self.assertEqual(priorities, expected)

        # Priorities are preserved when read from the schedule.
        items = self.scrooge.read_schedule(timestamp=eta)
        priorities = dict((t.id, t.priority) for t in items)
        self.assertEqual(priorities, expected)

    def test_periodic_priority(self):
        @self.scrooge.periodic_task(crontab(), priority=3, name="ptask")
        def task_p():
            pass

        self.task_0(0)
        self.task_1(10)
        self.task_2(100)

        for task in self.scrooge.read_periodic(datetime.datetime.now()):
            self.scrooge.enqueue(task)

        # Our periodic task has a higher priority than the other tasks in the
        # queue, and will be executed first.
        self.assertEqual(len(self.scrooge), 4)
        ptask = self.scrooge.dequeue()
        self.assertEqual(ptask.name, "ptask")  # Verify is our periodic task.
        self.assertEqual(ptask.priority, 3)  # Priority is preserved.

    def test_priority_retry(self):
        @self.scrooge.task(priority=3, retries=1)
        def task_3(n):
            raise ValueError("uh-oh")

        self.task_0(0)
        self.task_1(10)
        r2 = self.task_2(100)
        r3 = task_3(3)

        self.assertEqual(len(self.scrooge), 4)
        task = self.scrooge.dequeue()
        self.assertEqual(task.id, r3.id)
        self.assertEqual(task.priority, 3)
        self.assertEqual(task.retries, 1)
        self.assertTrue(self.scrooge.execute(task) is None)
        self.assertRaises(TaskException, r3.get)

        # Task has been re-enqueued for retry. Verify priority is preserved.
        self.assertEqual(len(self.scrooge), 4)
        rtask = self.scrooge.dequeue()
        self.assertEqual(rtask.id, r3.id)
        self.assertEqual(rtask.priority, 3)
        self.assertEqual(rtask.retries, 0)
        self.assertTrue(self.scrooge.execute(rtask) is None)

        # No more retries, now we'll get our task_2.
        self.assertEqual(len(self.scrooge), 3)
        task = self.scrooge.dequeue()
        self.assertEqual(task.id, r2.id)
