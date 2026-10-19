import multiprocessing
import threading
import time
import unittest
from typing import Optional

from larakit.pipeline import mp_apply, mp_stream

# Stands in for a lock the loader thread may hold while the workers start, like a module import lock
_LOCK = threading.Lock()
_lock_inherited: Optional[bool] = None


def _locking_generator(count: int):
    with _LOCK:
        time.sleep(.5)
    yield from range(count)


def _is_lock_inherited() -> bool:
    if _LOCK.acquire(timeout=1):
        _LOCK.release()
        return False
    return True


def _init_worker():
    global _lock_inherited  # pylint: disable=global-statement
    _lock_inherited = _is_lock_inherited()


def _get_lock_inherited(_) -> Optional[bool]:
    return _lock_inherited


def _stream_lock_inherited(_):
    yield _is_lock_inherited()


@unittest.skipUnless(multiprocessing.get_start_method() == 'fork', 'workers inherit locks only when forked')
class MultiprocessingForkTest(unittest.TestCase):
    def test_mp_apply_workers_do_not_inherit_loader_locks(self):
        results = list(mp_apply(_locking_generator(4), _get_lock_inherited, pool_init=_init_worker, threads=2))
        self.assertEqual([False] * 4, results)

    def test_mp_stream_workers_do_not_inherit_loader_locks(self):
        results = list(mp_stream(_locking_generator(4), _stream_lock_inherited, threads=2))
        self.assertEqual([False] * 4, results)
