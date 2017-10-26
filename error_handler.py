import functools
import logging
import graypy


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        gh = graypy.GELFHandler('69.195.152.133', 12201)
        logger.addHandler(logging.StreamHandler())
        #logger.addHandler(gh)
    return logger


def logexcept(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger('auttaja')
        try:
            return await func(*args, **kwargs)
        except:
            logger.exception(f"Exception occured in {func.__name__}")

    return wrapper
