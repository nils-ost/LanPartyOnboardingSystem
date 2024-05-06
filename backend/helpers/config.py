import os
import json


config = {
    'mongodb': {
        'host': 'localhost',
        'port': 27017,
        'database': 'LPOS'
    },
    'haproxy': {
        'host': '127.0.0.1',
        'api_port': 5555,
        'api_user': 'admin',
        'api_pw': 'adminpwd'
    },
    'server': {
        'port': 8000
    },
    'metrics': {
        'enabled': False,
        'port': 8001
    }
}

if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config.update(json.loads(f.read()))
else:
    with open('config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))


def reload_config():
    global config
    if os.path.isfile('config.json'):
        with open('config.json', 'r') as f:
            fconfig = json.load(f)
        for k in fconfig.keys():
            config[k].update(fconfig[k])
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


reload_config()
