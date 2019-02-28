import sys


def read_next_token(stdin):
    c = ' '
    while c.isspace():
        c = stdin.read(1)
    res = []
    while not c.isspace():
        res.append(c)
        c = stdin.read(1)
    return ''.join(res).strip()
