DEBUG_MODE = True


def print_debug(message):
    if DEBUG_MODE:
        print(message)


def assert_debug(cond):
    if not cond: 
        print_debug('fail')