import requests
import json
import logging
import subprocess
from helpers.docdb import docDB
from helpers.config import get_config

config = get_config('haproxy')
ssoproxycfg = """
global
        log /dev/log    local0
        log /dev/log    local1 notice
        stats socket ipv4@0.0.0.0:9999 level admin
        stats timeout 30s
        user haproxy
        group haproxy
        daemon

        # Default SSL material locations
        ca-base /etc/ssl/certs
        crt-base /etc/ssl/private

        # See: https://ssl-config.mozilla.org/#server=haproxy&server-version=2.0.3&config=intermediate
        ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:\
ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
        ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
        ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
        log     global
        mode    http
        option  httplog
        option  dontlognull
        timeout connect 5000
        timeout client  50000
        timeout server  50000


userlist haproxy-dataplaneapi
        user admin insecure-password adminpwd


program api
        command /usr/bin/dataplaneapi --host 0.0.0.0 --port 5555 --haproxy-bin /usr/sbin/haproxy -f /usr/local/etc/haproxy/dataplaneapi.yml \
--config-file /usr/local/etc/haproxy/haproxy.cfg --reload-cmd "kill -SIGUSR2 1" --restart-cmd "kill -SIGUSR2 1" --reload-delay 5 --userlist \
haproxy-dataplaneapi --scheme=http
        no option start-on-reload


frontend fe_sso
        bind :80
        mode tcp
        default_backend be_sso


frontend fe_sso_ssl
        bind :443
        mode tcp
        default_backend be_sso_ssl


backend be_sso
        mode tcp
        server online_sso 127.0.0.1:80 check


backend be_sso_ssl
        mode tcp
        option ssl-hello-chk
        server online_sso 127.0.0.1:443 check


frontend stats
        bind *:8404
        http-request use-service prometheus-exporter if { path /metrics }
        stats enable
        stats uri /stats
        stats refresh 10s
"""


class _BaseHAproxy():
    def __init__(self):
        self.container_id = None
        self._container_search_name = None
        self.config = {
            'host': '127.0.0.1',
            'api_port': 5555,
            'api_user': 'admin',
            'api_pw': 'adminpwd'
        }
        self.dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        self.init()

    def init(self):
        """
        overwrite with custom init, just a helper to omit calling super
        """
        pass

    def _get_api_session(self):
        s = requests.Session()
        s.auth = (self.config['api_user'], self.config['api_pw'])
        s.headers['Content-Type'] = 'application/json'
        url = f"http://{self.config['host']}:{self.config['api_port']}"
        return (s, url)

    def print_config(self):
        s, url = self._get_api_session()
        r = s.get(f'{url}/v2/services/haproxy/configuration/raw')
        for line in r.json()['data'].strip().split('\n'):
            print(line)

    def container_running(self):
        """
        Checks if the container, containing the HAproxy of search_name, is allready running
        """
        self.logger.info('checking if container is allready running')
        try:
            format = '\u007b\u007b.ID\u007d\u007d|\u007b\u007b.Names\u007d\u007d'
            cmd = f"{self.dcmd} ps --format='{format}' | grep {self._container_search_name}"
            self.container_id = subprocess.check_output(cmd, shell=True).decode('utf-8').split('|')[0]
            self.logger.info(f'container is running under id: {self.container_id}')
            return True
        except Exception:
            self.logger.info("container not started or can't be found")
            self.container_id = None
            return False

    def attach_ipvlan(self, name, int_ip):
        from elements import IpPool
        ip = IpPool.int_to_dotted(int_ip)
        self.logger.info(f"attaching ipvlan '{name}' with IP {ip}")
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return
        tmp_cmd = f'{self.dcmd} network inspect {name}'
        for k in json.loads(subprocess.check_output(tmp_cmd, shell=True).decode('utf-8').strip())[0]['Containers']:
            if k.startswith(self.container_id):
                self.logger.info(f"allready connected to ipvlan '{name}'")
                break  # haproxy allready connected to this vlan, for-else is not executed
        else:
            subprocess.call(f'{self.dcmd} network connect --ip={ip} {name} {self.container_id}', shell=True)

    def default_gateway(self, ip):
        self.logger.info(f'setting default gateway to {ip}')
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return
        subprocess.call(f'{self.dcmd} exec {self.container_id} ip route replace default via {ip}', shell=True)


class LPOSHAproxy(_BaseHAproxy):
    def init(self):
        global config
        self.logger = logging.getLogger('LPOS - HAproxy')
        self._container_search_name = 'haproxy'
        self.config = {
            'host': config['host'],
            'api_port': config['api_port'],
            'api_user': config['api_user'],
            'api_pw': config['api_pw']
        }
        self.container_running()

    def set_ms_redirect_url(self):
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return
        s, url = self._get_api_session()
        lpos_domain = 'http://' + '.'.join([docDB.get_setting('subdomain'), docDB.get_setting('domain')])
        self.logger.info(f'setting ms_redirect_url to {lpos_domain}')
        r = s.get(f'{url}/v2/services/haproxy/configuration/http_request_rules?parent_type=frontend&parent_name=fe_lpos')
        if r.status_code > 300:
            self.logger.error(f'requesting fe_lpos did not work:\n{r.text}')
            return
        o = r.json()

        data = dict()
        for d in o['data']:
            if d['cond_test'] == 'is_ms_redirect_url':
                data = d
        data['redir_value'] = lpos_domain

        cmd = f'{url}/v2/services/haproxy/configuration/http_request_rules/{data["index"]}?parent_type=frontend&parent_name=fe_lpos&version={o["_version"]}'
        r = s.put(cmd, data=json.dumps(data))
        if r.status_code > 300:
            self.logger.error(f'changing http_request_rule did not work:\n{r.text}')


class SSOHAproxy(_BaseHAproxy):
    def init(self):
        self.logger = logging.getLogger('SSO - HAproxy')
        self._container_search_name = 'lpos-ssoproxy'
        self.config = {
            'host': '127.0.0.1',
            'api_port': 5556,
            'api_user': 'admin',
            'api_pw': 'adminpwd'
        }
        self.container_running()

    def start_container(self):
        self.logger.info('starting container')
        if self.container_id is None and not self.container_running():
            try:
                open('/tmp/ssoproxy.cfg', 'w').write(ssoproxycfg)
                subprocess.call(f'{self.dcmd} run --rm --name copier-ssoproxy -v lpos-ssoproxy:/app -d alpine sleep 3', shell=True)
                subprocess.call(f'{self.dcmd} cp /tmp/ssoproxy.cfg copier-ssoproxy:/app/haproxy.cfg', shell=True)
                cmd = [
                    f'{self.dcmd} run --name lpos-ssoproxy --rm --cap-add=NET_ADMIN --sysctl net.ipv4.ip_unprivileged_port_start=0',
                    '-v lpos-ssoproxy:/usr/local/etc/haproxy/ -p 8405:8404 -p 127.0.0.1:5556:5555 -d haproxytech/haproxy-alpine:latest'
                ]
                self.container_id = subprocess.check_output(' '.join(cmd), shell=True).decode('utf-8').strip()
            except Exception as e:
                self.logger.error(f'could not start container\n{repr(e)}')
        else:
            self.logger.info(f'container is running under id: {self.container_id}')

    def setup_sso_ip(self):
        from urllib.parse import urlparse
        from helpers.client import nslookup
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return
        domain = urlparse(docDB.get_setting('sso_login_url')).netloc
        self.logger.info(f"adding configuration to proxy SSO logins on '{domain}' from onboarding networks to the internet")
        domain_ip = nslookup(domain)
        s, url = self._get_api_session()

        backends = ['be_sso', 'be_sso_ssl']
        for backend in backends:
            r = s.get(f'{url}/v2/services/haproxy/configuration/servers?backend={backend}').json()
            version = r['_version']
            for server in r['data']:
                if server['name'] == 'online_sso':
                    server['address'] = domain_ip
                    r = s.put(f'{url}/v2/services/haproxy/configuration/servers/online_sso?backend={backend}&version={version}', data=json.dumps(server))
                    if r.status_code > 300:
                        self.logger.error(f"updating server 'online_sso' on backend '{backend}' failed:\n{r.text}")
                    break


lposHAproxy = LPOSHAproxy()
ssoHAproxy = SSOHAproxy()
