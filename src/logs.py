import logging

logger = None


def get_logger():
    """Create or return the current logger."""
    global logger

    if logger is None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(name)s: %(asctime)s - %(levelname)s - '
            '%(funcName)s - Line %(lineno)d:\n'
            '    %(message)s'
        )

        fh = logging.FileHandler('dueturn.log', mode='w')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)

        fhDebug = logging.FileHandler(
            'dueturn_debug.log', mode='w')
        fhDebug.setLevel(logging.DEBUG)
        fhDebug.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(fhDebug)

    return logger
