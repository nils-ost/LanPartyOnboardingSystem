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


def default_gateway(ip):
    logger.info(f'setting default gateway to {ip}')
    dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
    try:
        format = '\u007b\u007b.ID\u007d\u007d|\u007b\u007b.Image\u007d\u007d|\u007b\u007b.Names\u007d\u007d'
        hap_container = subprocess.check_output(f"{dcmd} ps --format='{format}' | grep haproxy", shell=True).decode('utf-8').split('|')[0]
        subprocess.call(f'{dcmd} exec {hap_container} ip route replace default via {ip}', shell=True)
    except Exception:
        logger.warning("haproxy container not started or can't be found")


def setup_sso_login_proxy():
    from urllib.parse import urlparse
    from helpers.client import nslookup
    from helpers.system import get_use_nlpt_sso
    if not get_use_nlpt_sso():
        logger.info('configuration to proxy SSO logins from onboarding networks to the internet not needed, as SSO is not used')
        return
    domain = urlparse(docDB.get_setting('sso_login_url')).netloc
    logger.info(f"adding configuration to proxy SSO logins on '{domain}' from onboarding networks to the internet")
    domain_ip = nslookup(domain)
    if domain_ip is None:
        logger.error(f"could not determine IP for domain '{domain}'")
        return
    s, url = _get_session()

    # configure backend 'be_sso'
    r = s.get(f'{url}/v2/services/haproxy/configuration/backends').json()
    for backend in r['data']:
        if backend['name'] == 'be_sso':
            break
    else:
        version = r['_version']
        data = {'name': 'be_sso'}
        r = s.post(f'{url}/v2/services/haproxy/configuration/backends?version={version}', data=json.dumps(data))
        if r.status_code > 300:
            logger.error(f"creating backend 'be_sso' failed:\n{r.text}")
            return

    # configure server 'online_sso' on backend 'be_sso'
    r = s.get(f'{url}/v2/services/haproxy/configuration/servers?backend=be_sso').json()
    version = r['_version']
    data = {'name': 'online_sso', 'address': domain_ip, 'check': 'enabled', 'health_check_port': 80}
    for server in r['data']:
        if server['name'] == 'online_sso':
            # update server
            r = s.put(f'{url}/v2/services/haproxy/configuration/servers/online_sso?backend=be_sso&version={version}', data=json.dumps(data))
            if r.status_code > 300:
                logger.error(f"updating server 'online_sso' on backend 'be_sso' failed:\n{r.text}")
                return
            break
    else:
        # create server
        r = s.post(f'{url}/v2/services/haproxy/configuration/servers?backend=be_sso&version={version}', data=json.dumps(data))
        if r.status_code > 300:
            logger.error(f"creating server 'online_sso' on backend 'be_sso' failed:\n{r.text}")
            return

    # configure frontend rule to redirect traffic on domain to 'be_sso'
    r = s.get(f'{url}/v2/services/haproxy/configuration/backend_switching_rules?frontend=fe_lpos').json()
    version = r['_version']
    data = {'index': len(r['data']), 'name': 'be_sso', 'cond': 'if', 'cond_test': f'\u007b hdr(host) -i {domain} \u007d'}
    for rule in r['data']:
        if rule['name'] == 'be_sso':
            # update rule
            index = rule['index']
            data['index'] = index
            r = s.put(f'{url}/v2/services/haproxy/configuration/backend_switching_rules/{index}?version={version}&frontend=fe_lpos', data=json.dumps(data))
            if r.status_code > 300:
                logger.error(f"updating switching_rule on frontend 'fe_lpos' for backend 'be_sso' failed:\n{r.text}")
                return
            break
    else:
        # create rule
        r = s.post(f'{url}/v2/services/haproxy/configuration/backend_switching_rules?version={version}&frontend=fe_lpos', data=json.dumps(data))
        if r.status_code > 300:
            logger.error(f"creating switching_rule on frontend 'fe_lpos' for backend 'be_sso' failed:\n{r.text}")
            return


class LPOSHAproxy():
    def __init__(self):
        pass


class SSOHAproxy():
    def __init__(self):
        self.logger = logging.getLogger('SSO - HAproxy')
        self.container_running()

    def container_running(self):
        """
        Checks if the container, containing the HAproxy for online-sso, is allready running
        """
        self.logger.info('checking if container is allready running')
        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        try:
            format = '\u007b\u007b.ID\u007d\u007d|\u007b\u007b.Names\u007d\u007d'
            self.container_id = subprocess.check_output(f"{dcmd} ps --format='{format}' | grep lpos-ssoproxy", shell=True).decode('utf-8').split('|')[0]
            self.logger.info(f'container is running under id: {self.container_id}')
            return True
        except Exception:
            self.logger.info("container not started or can't be found")
            self.container_id = None
            return False

    def start_container(self):
        pass

    def attach_ipvlan(self, name, int_ip):
        from elements import IpPool
        ip = IpPool.int_to_dotted(int_ip)
        logger.info(f"attaching ipvlan '{name}' with IP {ip}")
        if self.container_id is None and not self.container_running():
            logger.warning("container not started or can't be found")
            return
        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        tmp_cmd = f'{dcmd} network inspect {name}'
        for k in json.loads(subprocess.check_output(tmp_cmd, shell=True).decode('utf-8').strip())[0]['Containers']:
            if k.startswith(self.container_id):
                logger.info(f"allready connected to ipvlan '{name}'")
                break  # haproxy allready connected to this vlan, for-else is not executed
        else:
            subprocess.call(f'{dcmd} network connect --ip={ip} {name} {self.container_id}', shell=True)


lposHAproxy = LPOSHAproxy()
ssoHAproxy = SSOHAproxy()
