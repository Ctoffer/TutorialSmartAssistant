from json import load as json_load
from types import SimpleNamespace


def load_config(path):
    with open(path, 'r', encoding='utf-8') as fp:
        json_dict = json_load(fp)

    return dict_to_simple_namespace(json_dict)


def dict_to_simple_namespace(d) -> SimpleNamespace:
    if type(d) is not dict:
        return d
    return SimpleNamespace(**{key:dict_to_simple_namespace(value) for key, value in d.items()})