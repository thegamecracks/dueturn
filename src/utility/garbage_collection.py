import gc
from src import logs

logger = logs.get_logger()


def collect_and_log_garbage(log_handler=None):
    garbageCollection = gc.get_stats()
    garbageCollectionLog = '\n'.join(
        [f'Generation {n}: {repr(d)}'
         for n, d in enumerate(garbageCollection)])
    if log_handler is not None:
        logger.debug(
            'Logging garbage collection:\n' + garbageCollectionLog)
    return garbageCollectionLog
