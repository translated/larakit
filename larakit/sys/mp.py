import multiprocessing
import threading
from queue import Queue


def mp_apply(generator, fn, pool_init=None, pool_init_args=None, batch_size=1, ordered=True, threads=None):
    cores = threads or multiprocessing.cpu_count()

    def loader(generator_, jobs_):
        for args in generator_:
            jobs_.put(args, block=True)
        jobs_.put(None, block=True)

    jobs = Queue(maxsize=cores * batch_size)
    loader_thread = threading.Thread(target=loader, args=(generator, jobs), daemon=True)

    loader_thread.start()

    with multiprocessing.Pool(initializer=pool_init, initargs=pool_init_args, processes=cores) as pool:
        imap_f = pool.imap if ordered else pool.imap_unordered

        for result in imap_f(fn, iter(jobs.get, None), chunksize=batch_size):
            yield result

    loader_thread.join()
