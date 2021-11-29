# -*- coding: utf-8 -*-
# 记录错误的装饰器
import time
from functools import wraps


def retry(logger=None, tries=3, delay=2, backoff=2):
    """
    Decorator that catches exceptions and automatically retry
    Args:
        logger: Logger
        tries: max retry times
        delay: time interval of first retry
        backoff:

    Returns:

    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    msg = f'{e}, Retring in {mdelay} seconds...'
                    if logger:
                        if mtries > 1:
                            logger.warning(msg)
                        else:
                            logger.error(e)
                            raise e
                    else:
                        raise e
                time.sleep(mdelay)
                mtries -= 1
                mdelay *= backoff
        return wrapper
    return decorator
