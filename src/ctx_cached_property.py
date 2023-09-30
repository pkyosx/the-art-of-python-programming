# TAG: descriptor, contextlib, contextvars
#
# This example leverage descriptor, contextlib and contextvars to implement a cached property
# A cache with controlled lifecycle is pretty useful in some cases
# eg. we can put the under_ctx() in middleware to cache some data for each request
#     this way we can avoid duplicate computation for the same request
#     and we can also avoid the problem of cache re-use between requests

# ref: https://docs.python.org/3/howto/descriptor.html
# ref: https://docs.python.org/3/library/contextlib.html
# ref: https://docs.python.org/3/library/contextvars.html

from contextlib import contextmanager
from contextvars import ContextVar

# make cache_holder a thread / coroutine local variable
cache_holder = ContextVar('cache_holder')

class ctx_cached_property:
    def __init__(self, func):
        self._func = func

    def calc_cache_key(self, instance):
        # each instance has its own cache
        return f"{id(instance)} {self._func}"

    def __get__(self, instance, instance_class=None):
        if instance is None:
            # get here when we call Foo.bar
            return self

        try:
            cache = cache_holder.get()
        except LookupError:
            # get here when we call Foo().bar without under_ctx()
            # you can also choose to raise an error here if a ctx is expected to exist
            print(f"warning: cache does not work for {self._func} outside context")
            return self._func(instance)

        cache_key = self.calc_cache_key(instance)
        if cache_key not in cache:
            cache[cache_key] = self._func(instance)
        return cache[cache_key]

@contextmanager
def under_ctx():
    token = cache_holder.set({})
    try:
        yield
    finally:
        cache_holder.reset(token)

def main():
    class Foo:
        def __init__(self):
            self._bar = 0

        @ctx_cached_property
        def bar(self):
            self._bar += 1
            return self._bar

    foo = Foo()

    with under_ctx():
        assert foo.bar == 1
        assert foo.bar == 1
    assert foo.bar == 2

if __name__ == '__main__':
    main()