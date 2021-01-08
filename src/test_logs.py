import logs


def test_logging():
    logger = logs.get_logger()
    logger.debug('pytest log')
