import re

def join_url(*args):
    s = '/'.join(args)
    return re.sub(r'/+', '/', s)
