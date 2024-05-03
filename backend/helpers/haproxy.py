import requests
import json
import logging
import subprocess
from helpers.docdb import docDB
from helpers.config import get_config

logger = logging.getLogger(__name__)
config = get_config('haproxy')


def _get_session():
    s = requests.Session()
    s.auth = (config['api_user'], config['api_pw'])
    s.headers['Content-Type'] = 'application/json'
    url = f"http://{config['host']}:{config['api_port']}"
    return (s, url)


def print_config():
    s, url = _get_session()
    r = s.get(f'{url}/v2/services/haproxy/configuration/raw')
    for line in r.json()['data'].strip().split('\n'):
        print(line)


def set_ms_redirect_url():
    s, url = _get_session()
    lpos_domain = 'http://' + '.'.join([docDB.get_setting('subdomain'), docDB.get_setting('domain')])
    logger.info(f'setting ms_redirect_url to {lpos_domain}')
    r = s.get(f'{url}/v2/services/haproxy/configuration/http_request_rules?parent_type=frontend&parent_name=fe_lpos')
    if r.status_code > 300:
        logger.error(f'requesting fe_lpos did not work:\n{r.text}')
    o = r.json()

    data = dict()
    for d in o['data']:
        if d['cond_test'] == 'is_ms_redirect_url':
            data = d

    data['redir_value'] = lpos_domain

    cmd = f'{url}/v2/services/haproxy/configuration/http_request_rules/{data["index"]}?parent_type=frontend&parent_name=fe_lpos&version={o["_version"]}'
    r = s.put(cmd, data=json.dumps(data))
    if r.status_code > 300:
        logger.error(f'changing http_request_rule did not work:\n{r.text}')


def attach_ipvlan(name, int_ip):
    from elements import IpPool
    ip = IpPool.int_to_dotted(int_ip)
    logger.info(f"attaching ipvlan '{name}' to haproxy, with IP {ip}")
    dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
    try:
        format = '\u007b\u007b.ID\u007d\u007d|\u007b\u007b.Image\u007d\u007d|\u007b\u007b.Names\u007d\u007d'
        hap_container = subprocess.check_output(f"{dcmd} ps --format='{format}' | grep haproxy", shell=True).decode('utf-8').split('|')[0]
        tmp_cmd = f'{dcmd} network inspect {name}'
        for k in json.loads(subprocess.check_output(tmp_cmd, shell=True).decode('utf-8').strip())[0]['Containers']:
            if k.startswith(hap_container):
                logger.info(f"haproxy allready connected to ipvlan '{name}'")
                break  # haproxy allready connected to this vlan, for-else is not executed
        else:
            subprocess.call(f'{dcmd} network connect --ip={ip} {name} {hap_container}', shell=True)
    except Exception:
        logger.warning("haproxy container not started or can't be found")
        pass
