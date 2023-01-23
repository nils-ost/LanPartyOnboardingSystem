import os
import json


config = {
    'mongodb': {
        'host': 'localhost',
        'port': 27017,
        'database': 'LPOS'
    },
    'server': {
        'port': 8000
    }
}

if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config.update(json.loads(f.read()))
else:
    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))


def get_config(portion=None):
    global config
    if portion is None:
        return config
    else:
        return config.get(portion, None)


def set_config(nconfig, portion=None):
    global config
    if portion is None:
        config = nconfig
    else:
        config[portion] = nconfig
    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))
