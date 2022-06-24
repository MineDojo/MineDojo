import socket
import logging
import functools

import Pyro4


retry_count = 20
logger = logging.getLogger(__name__)


def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retry_exc = None
        for i in range(retry_count):
            try:
                return func(*args, **kwargs)
            except Pyro4.errors.PyroError as e:
                logger.error(
                    "An error occurred contacting the instance manager. Is it started!?"
                )
                raise e
            except (socket.timeout, socket.error, RuntimeError) as e:
                if retry_exc is None:
                    retry_exc = e
                if i < retry_count - 1:
                    logger.debug(f"Pause before retry on " + str(e))
                    raise e
        raise retry_exc

    return wrapper
