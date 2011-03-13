from functools import wraps
from flask import request
from google.appengine.api import memcache
import logging


def cached(cache_key, timeout = 5 * 60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rv = memcache.get(cache_key)
            if rv is not None:
                logging.info("Found key %s in memcache" % cache_key)
                return rv
            rv = f(*args, **kwargs)
            memcache.set(cache_key, rv, timeout)
            return rv
        return decorated_function
    return decorator


def cached_route(timeout=5 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = memcache.get(cache_key)
            if rv is not None:
                logging.info("Found route %s in memcache" % cache_key)
                return rv
            rv = f(*args, **kwargs)
            memcache.set(cache_key, rv, timeout)
            return rv
        return decorated_function
    return decorator
