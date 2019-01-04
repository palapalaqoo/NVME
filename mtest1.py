from __future__ import print_function

try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__
    
def print(*args, **kwargs):
    """My custom print() function."""
    # Adding new arguments to the print function signature 
    # is probably a bad idea.
    # Instead consider testing if custom argument keywords
    # are present in kwargs
    __builtin__.print('My overridden print() function!')
    return __builtin__.print(*args, **kwargs)