import functools
import logging


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())
    return logger


def logexcept(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger('auttaja')
        try:
            return await func(*args, **kwargs)
        except BaseException as e:
            logger.exception(f"Exception occured in {func.__name__}")

    return wrapper
