# Scrooge

Scrooge is a fork of the Huey project, modified to fit our needs.

scrooge supports:

* multi-process, multi-thread or greenlet task execution models
* schedule tasks to execute at a given time, or after a given delay
* schedule recurring tasks, like a crontab
* automatically retry tasks that fail
* task prioritization
* task result storage
* task expiration
* task locking
* task pipelines and chains

At a glance
-----------

.. code-block:: python

    from scrooge import RedisScrooge, crontab

    scrooge = RedisScrooge('my-app', host='redis.myapp.com')

    @scrooge.task()
    def add_numbers(a, b):
        return a + b

    @scrooge.task(retries=2, retry_delay=60)
    def flaky_task(url):
        # This task might fail, in which case it will be retried up to 2 times
        # with a delay of 60s between retries.
        return this_might_fail(url)

    @scrooge.periodic_task(crontab(minute='0', hour='3'))
    def nightly_backup():
        sync_all_data()

Calling a ``task``-decorated function will enqueue the function call for
execution by the consumer. A special result handle is returned immediately,
which can be used to fetch the result once the task is finished:

.. code-block:: pycon

    >>> from demo import add_numbers
    >>> res = add_numbers(1, 2)
    >>> res
    <Result: task 6b6f36fc-da0d-4069-b46c-c0d4ccff1df6>

    >>> res()
    3

Tasks can be scheduled to run in the future:

.. code-block:: pycon

    >>> res = add_numbers.schedule((2, 3), delay=10)  # Will be run in ~10s.
    >>> res(blocking=True)  # Will block until task finishes, in ~10s.
    5

For much more, check out the `guide <https://scrooge.readthedocs.io/en/latest/guide.html>`_
or take a look at the `example code <https://github.com/coleifer/scrooge/tree/master/examples/>`_.

Running the consumer
^^^^^^^^^^^^^^^^^^^^

Run the consumer with four worker processes:

.. code-block:: console

    $ scrooge_consumer.py my_app.scrooge -k process -w 4

To run the consumer with a single worker thread (default):

.. code-block:: console

    $ scrooge_consumer.py my_app.scrooge

If your work-loads are mostly IO-bound, you can run the consumer with threads
or greenlets instead. Because greenlets are so lightweight, you can run quite a
few of them efficiently:

.. code-block:: console

    $ scrooge_consumer.py my_app.scrooge -k greenlet -w 32

Storage
-------

Scrooge's design and feature-set were informed by the capabilities of the
`Redis <https://redis.io>`_ database. Redis is a fantastic fit for a
lightweight task queueing library like Scrooge: it's self-contained, versatile,
and can be a multi-purpose solution for other web-application tasks like
caching, event publishing, analytics, rate-limiting, and more.

Although Scrooge was designed with Redis in mind, the storage system implements a
simple API and many other tools could be used instead of Redis if that's your
preference.

Scrooge comes with builtin support for Redis, Sqlite and in-memory storage.

Documentation
----------------

`See Scrooge documentation <https://scrooge.readthedocs.io/>`_.

Project page
---------------

`See source code and issue tracker on Github <https://github.com/coleifer/scrooge/>`_.

Scrooge is named in honor of my cat:

.. image:: http://m.charlesleifer.com/t/800x-/blog/photos/p1473037658.76.jpg?key=mD9_qMaKBAuGPi95KzXYqg

