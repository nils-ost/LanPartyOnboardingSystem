import requests
import json
import time
import logging
import docker
from elements import Setting

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
        self.dcli = docker.from_env()
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
        dcon = self.dcli.containers.list(filters={'name': self._container_search_name})
        if len(dcon) > 0:
            self.container_id = dcon[0].id
            self.logger.info(f'container is running under id: {self.container_id}')
            return True
        else:
            self.logger.info("container not started or can't be found")
            self.container_id = None
            return False

    def wait_for_running(self, timeout=5):
        count = 0
        while True:
            if count >= timeout:
                return False
            try:
                s, url = self._get_api_session()
                r = s.get(f'{url}/services/haproxy/stats/native')
                if r.status_code == 200:
                    return True
                time.sleep(1)
            except Exception:
                time.sleep(1)
            count += 1

    def attach_ipvlan(self, name, int_ip):
        from elements import IpPool
        ip = IpPool.int_to_dotted(int_ip)
        self.logger.info(f"attaching ipvlan '{name}' with IP {ip}")
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return

        try:
            dnet = self.dcli.networks.get(name)
            for dcon in dnet.containers:
                if dcon.id == self.container_id:
                    break  # haproxy allready connected to this vlan, for-else is not executed
            else:
                dnet.connect(self.container_id, ipv4_address=ip)
        except docker.errors.NotFound:
            self.logger.error(f"can't find network with name: {name}")

    def execute_command(self, cmd):
        self.logger.info(f"execute command '{cmd}'")
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return ''
        return self.dcli.containers.get(self.container_id).exec_run(cmd).output.decode('utf-8')

    def default_gateway(self, ip):
        self.logger.info(f'setting default gateway to {ip}')
        self.execute_command(f'ip route replace default via {ip}')


class LPOSHAproxy(_BaseHAproxy):
    def init(self):
        global config
        self.logger = logging.getLogger('LPOS - HAproxy')
        self._container_search_name = 'haproxy'
        self.config = {
            'host': Setting.value('haproxy_api_host'),
            'api_port': Setting.value('haproxy_api_port'),
            'api_user': Setting.value('haproxy_api_user'),
            'api_pw': Setting.value('haproxy_api_pw')
        }
        self.container_running()

    def set_ms_redirect_url(self):
        from elements import Setting
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return False
        s, url = self._get_api_session()
        lpos_domain = 'http://' + '.'.join([Setting.value('subdomain'), Setting.value('domain')])
        self.logger.info(f'setting ms_redirect_url to {lpos_domain}')
        r = s.get(f'{url}/v2/services/haproxy/configuration/http_request_rules?parent_type=frontend&parent_name=fe_lpos')
        if r.status_code > 300:
            self.logger.error(f'requesting fe_lpos did not work:\n{r.text}')
            return False
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
            return False
        return True


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
        import tempfile
        import tarfile
        import os
        import pathlib
        self.logger.info('starting container')
        if self.container_id is None and not self.container_running():
            # create a temporary container, to inject configuration to volume
            copier_con = self.dcli.containers.run(
                name='copier-ssoproxy',
                image='alpine',
                command='sleep 3',
                volumes=['lpos-ssoproxy:/app:rw'],
                remove=True,
                detach=True
            )

            # place configuration into volume, using temporary container
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = pathlib.Path(temp_dir)

                with open(os.path.join(temp_path, 'haproxy.cfg'), 'w') as ssoproxyfile:
                    ssoproxyfile.write(ssoproxycfg)

                with tempfile.TemporaryFile(suffix='.tar') as archive:
                    with tarfile.open(fileobj=archive, mode='w') as tar:
                        tar.add(os.path.join(temp_path, 'haproxy.cfg'), 'haproxy.cfg')
                    archive.flush()
                    archive.seek(0)

                    copier_con.put_archive('/app/', archive)

            # create and start container
            dcon = self.dcli.containers.run(
                name='lpos-ssoproxy',
                image='haproxytech/haproxy-alpine:latest',
                volumes=['lpos-ssoproxy:/usr/local/etc/haproxy/:rw'],
                cap_add=['NET_ADMIN'],
                sysctls={'net.ipv4.ip_unprivileged_port_start': 0},
                ports={
                    '8404/tcp': '8405',
                    '5555/tcp': '127.0.0.1:5556'
                },
                restart_policy={'Name': 'always'},
                detach=True,
                remove=True
            )
            self.container_id = dcon.id
            self.logger.info(f'container started with id: {self.container_id}')
        else:
            self.logger.info(f'container is running under id: {self.container_id}')
        return True

    def setup_sso_ip(self):
        from urllib.parse import urlparse
        from helpers.client import nslookup
        from elements import Setting
        if self.container_id is None and not self.container_running():
            self.logger.warning("container not started or can't be found")
            return False
        domain = urlparse(Setting.value('sso_login_url')).netloc
        self.logger.info(f"adding configuration to proxy SSO logins on '{domain}' from onboarding networks to the internet")
        domain_ip = Setting.value('sso_ip_overwrite')
        if domain_ip is None:
            domain_ip = nslookup(domain)
        self.logger.info(f"forwarding SSO logins to '{domain_ip}'")
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
                        return False
                    break
        return True


lposHAproxy = LPOSHAproxy()
ssoHAproxy = SSOHAproxy()
