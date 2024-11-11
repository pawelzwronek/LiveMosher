import builtins
import datetime

_print = builtins.print

def _custom_print(*args, **kwargs):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4] + ':'
    _print(timestamp, *args, **kwargs)

def print(*args, **kwargs): # pylint: disable=redefined-builtin
    _custom_print(*args, **kwargs)

def print_warn(*args, **kwargs):
    _print('\033[33m', end='')
    print(*args, **kwargs, end='')
    _print('\033[0m')

def print_error(*args, **kwargs):
    _print('\033[91m', end='')
    print(*args, **kwargs, end='')
    _print('\033[0m')

if builtins.print != _custom_print: # pylint: disable=comparison-with-callable
    builtins.print = _custom_print
