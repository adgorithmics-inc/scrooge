import sys
import traceback
from functools import wraps
from importlib import import_module

from django.conf import settings
from django.db import close_old_connections, transaction

configuration_message = """
Configuring Scrooge for use with Django
====================================

Scrooge was designed to be simple to configure in the general case.  For that
reason, scrooge will "just work" with no configuration at all provided you have
Redis installed and running locally.

On the other hand, you can configure scrooge manually using the following
setting structure.

The following example uses Redis on localhost, and will run four worker
processes:

SCROOGE = {
    'name': 'my-app',
    'connection': {'host': 'localhost', 'port': 6379},
    'consumer': {
        'workers': 4,
        'worker_type': 'process',  # "thread" or "greenlet" are other options
    },
}

If you would like to configure Scrooge's logger using Django's integrated logging
settings, the logger used by consumer is named "scrooge".

Alternatively you can simply assign `settings.SCROOGE` to an actual `Scrooge`
object instance:

from scrooge import RedisScrooge
SCROOGE = RedisScrooge('my-app')
"""


default_backend_path = "scrooge.RedisScrooge"


def default_queue_name():
    try:
        return settings.DATABASE_NAME
    except AttributeError:
        try:
            return str(settings.DATABASES["default"]["NAME"])
        except KeyError:
            return "scrooge"


def get_backend(import_path=default_backend_path):
    module_path, class_name = import_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


def config_error(msg):
    print(configuration_message)
    print("\n\n")
    print(msg)
    sys.exit(1)


SCROOGE = getattr(settings, "SCROOGE", None)
if SCROOGE is None:
    try:
        RedisScrooge = get_backend(default_backend_path)
    except ImportError:
        config_error(
            "Error: Scrooge could not import the redis backend. " "Install `redis-py`."
        )
    else:
        SCROOGE = RedisScrooge(default_queue_name())

if isinstance(SCROOGE, dict):
    scrooge_config = SCROOGE.copy()  # Operate on a copy.
    name = scrooge_config.pop("name", default_queue_name())
    if "backend_class" in scrooge_config:
        scrooge_config["scrooge_class"] = scrooge_config.pop("backend_class")
    backend_path = scrooge_config.pop("scrooge_class", default_backend_path)
    conn_kwargs = scrooge_config.pop("connection", {})
    try:
        del scrooge_config["consumer"]  # Don't need consumer opts here.
    except KeyError:
        pass
    if "immediate" not in scrooge_config:
        scrooge_config["immediate"] = settings.DEBUG
    scrooge_config.update(conn_kwargs)

    try:
        backend_cls = get_backend(backend_path)
    except (ValueError, ImportError, AttributeError):
        config_error(
            "Error: could not import Scrooge backend:\n%s" % traceback.format_exc()
        )

    SCROOGE = backend_cls(name, **scrooge_config)

# Function decorators.
task = SCROOGE.task
periodic_task = SCROOGE.periodic_task
lock_task = SCROOGE.lock_task

# Task management.
enqueue = SCROOGE.enqueue
restore = SCROOGE.restore
restore_all = SCROOGE.restore_all
restore_by_id = SCROOGE.restore_by_id
revoke = SCROOGE.revoke
revoke_all = SCROOGE.revoke_all
revoke_by_id = SCROOGE.revoke_by_id
is_revoked = SCROOGE.is_revoked
result = SCROOGE.result
scheduled = SCROOGE.scheduled

# Hooks.
on_startup = SCROOGE.on_startup
on_shutdown = SCROOGE.on_shutdown
pre_execute = SCROOGE.pre_execute
post_execute = SCROOGE.post_execute
signal = SCROOGE.signal
disconnect_signal = SCROOGE.disconnect_signal


def close_db(fn):
    """Decorator to be used with tasks that may operate on the database."""

    @wraps(fn)
    def inner(*args, **kwargs):
        if not SCROOGE.immediate:
            close_old_connections()
        try:
            return fn(*args, **kwargs)
        finally:
            if not SCROOGE.immediate:
                close_old_connections()

    return inner


def db_task(*args, **kwargs):
    def decorator(fn):
        ret = task(*args, **kwargs)(close_db(fn))
        ret.call_local = fn
        return ret

    return decorator


def db_periodic_task(*args, **kwargs):
    def decorator(fn):
        ret = periodic_task(*args, **kwargs)(close_db(fn))
        ret.call_local = fn
        return ret

    return decorator


def on_commit_task(*args, **kwargs):
    """
    This task will register a post-commit callback to enqueue the task. A
    result handle will still be returned immediately, however, even though
    the task may not (ever) be enqueued, subject to whether or not the
    transaction actually commits.

    Because we have to setup the callback within the bit of code that performs
    the actual enqueueing, we cannot expose the full functionality of the
    TaskWrapper. If you anticipate wanting all these methods, you are probably
    best off decorating the same function twice, e.g.:

        def update_data(pk):
            # Do some database operation.
            pass

        my_task = task()(update_data)
        my_on_commit_task = on_commit_task()(update_data)
    """

    def decorator(fn):
        task_wrapper = task(*args, **kwargs)(close_db(fn))

        @wraps(fn)
        def inner(*a, **k):
            task = task_wrapper.s(*a, **k)

            def enqueue_on_commit():
                task_wrapper.scrooge.enqueue(task)

            transaction.on_commit(enqueue_on_commit)
            return SCROOGE._result_handle(task)

        return inner

    return decorator
