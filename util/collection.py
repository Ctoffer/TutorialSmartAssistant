from collections import defaultdict


def group(iterable, key):
    result = defaultdict(list)
    for element in iterable:
        result[key(element)].append(element)
    return result