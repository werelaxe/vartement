import sys


def read_next_token():
    c = ' '
    while c.isspace():
        c = sys.stdin.read(1)
    res = []
    while not c.isspace():
        res.append(c)
        c = sys.stdin.read(1)
    return ''.join(res).strip()
