import time
import random
import logging
import requests

logger = logging.getLogger(__name__)

class retry(object):
    def __init__(self, max_attempts):
        self.max_attempts = max_attempts
    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            attempt = 1
            while True:
                try:
                    f(*args, **kwargs)
                    break
                except requests.exceptions.ConnectionError as e:
                    attempt += 1
                    if attempt == self.max_attempts + 1:
                        raise RetryError("maximum retries exceeded")
                    seconds = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                    message = "sleeping for {0} seconds before retry {1}/{2} due to error {3}"
                    logger.warn(message.format(seconds, attempt, self.max_attempts, e))
                    time.sleep(seconds)
                else:
                    raise e
        return wrapped_f

class RetryError(Exception):
    pass
