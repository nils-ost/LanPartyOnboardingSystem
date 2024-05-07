import json
import subprocess
from elements._elementBase import ElementBase, docDB


class VLAN(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, unique=True, notnone=True),
        purpose=ElementBase.addAttr(type=int, default=3, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True)
    )

    @classmethod
    def get_by_number(cls, number):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'number': number})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_purpose(cls, number):
        result = list()
        for fromdb in docDB.search_many(cls.__name__, {'purpose': number}):
            r = cls()
            r._attr = fromdb
            result.append(r)
        return result

    def validate(self):
        errors = dict()
        if self['number'] not in range(1, 1025):
            errors['number'] = {'code': 10, 'desc': 'needs to be a value from 1 to 1024'}
        if self['purpose'] not in range(4):
            errors['purpose'] = {'code': 11, 'desc': 'needs to be 0, 1, 2 or 3'}
        if self['purpose'] in range(2):
            found = docDB.search_one(self.__class__.__name__, {'_id': {'$ne': self['_id']}, 'purpose': self['purpose']})
            if found is not None:
                errors['purpose'] = {'code': 12, 'desc': f"values 0 and 1 need to be unique, but element with value {self['purpose']} allready present"}
        return errors

    def delete_pre(self):
        if docDB.search_one('IpPool', {'vlan_id': self['_id']}) is not None:
            return {'error': {'code': 1, 'desc': 'at least one IpPool is using this VLAN'}}
        if docDB.search_one('Switch', {'onboarding_vlan_id': self['_id']}) is not None:
            return {'error': {'code': 4, 'desc': 'at least one Switch is using this VLAN'}}
        from elements import Switch
        for switch in Switch.all():
            switch.remove_vlan(self['number'])

    def commit_os_interface(self):
        from elements import IpPool
        from helpers.system import check_integrity_vlan_interface_commit
        from helpers.haproxy import attach_ipvlan as hap_attach_ipvlan, default_gateway as hap_default_gateway, setup_sso_login_proxy as hap_sso_proxy
        integrity = check_integrity_vlan_interface_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
            return True  # does not get an interface
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        pool = IpPool.get_by_vlan(self['_id'])
        if len(pool) == 0:
            return False  # no needed pool defined
        pool = pool[0]

        iname = docDB.get_setting('os_nw_interface')
        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'

        if not 0 == subprocess.call(f'{dcmd} network ls | grep lpos-ipvlan{self["number"]}', shell=True):
            # vlan not yet defined, defining it
            subnet = f'{pool.subnet_ip(dotted=True)}/{pool["mask"]}'
            subprocess.call(f'{dcmd} network create -d ipvlan --subnet={subnet} -o parent={iname}.{self["number"]} lpos-ipvlan{self["number"]}', shell=True)

        # depending on the vlan-purpose configure haproxy
        if self['purpose'] == 0:
            hap_attach_ipvlan(f"lpos-ipvlan{self['number']}", IpPool.get_lpos()['range_start'])
            hap_default_gateway(docDB.get_setting('play_gateway'))
            hap_sso_proxy()
        else:
            hap_attach_ipvlan(f"lpos-ipvlan{self['number']}", pool['range_start'] + 1)

        return True

    def retreat_os_interface(self):
        if self['purpose'] in [1, 3]:
            return True  # does not got an interface
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        if not 0 == subprocess.call(f'{dcmd} network ls | grep lpos-ipvlan{self["number"]}', shell=True):
            return True  # allready removed

        # unbind vlan from HAproxy
        try:
            format = '\u007b\u007b.ID\u007d\u007d|\u007b\u007b.Image\u007d\u007d|\u007b\u007b.Names\u007d\u007d'
            hap_container = subprocess.check_output(f"sudo docker ps --format='{format}' | grep haproxy", shell=True).decode('utf-8').split('|')[0]
            tmp_cmd = f'{dcmd} network inspect lpos-ipvlan{self["number"]}'
            for k in json.loads(subprocess.check_output(tmp_cmd, shell=True).decode('utf-8').strip())[0]['Containers']:
                if k.startswith(hap_container):
                    # haproxy is connected to this vlan, disconnecting haproxy
                    subprocess.call(f'{dcmd} network disconnect lpos-ipvlan{self["number"]} {hap_container}', shell=True)
        except Exception:
            pass  # haproxy container not started or can't be found, skipping this step

        subprocess.call(f'{dcmd} network rm lpos-ipvlan{self["number"]}', shell=True)
        return True

    def commit_dns_server(self):
        from elements import IpPool
        from helpers.system import check_integrity_vlan_dns_commit, get_use_nlpt_sso
        integrity = check_integrity_vlan_dns_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [0, 1, 3]:
            return True  # does not get a dns server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        pool = IpPool.get_by_vlan(self['_id'])
        if len(pool) == 0:
            return False  # no needed pool defined
        pool = pool[0]

        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        if not 0 == subprocess.call(f'{dcmd} network ls | grep lpos-ipvlan{self["number"]}', shell=True):
            return False  # VLAN not defined, can't start DNS-Server

        if not 0 == subprocess.call(f'{dcmd} ps --format=\u007b\u007b.Names\u007d\u007d | grep lpos-ipvlan{self["number"]}-dns', shell=True):
            # DNS-Server not yet started, configuring and starting it
            lpos_domain = '.'.join([docDB.get_setting('subdomain'), docDB.get_setting('domain')])
            lpos_ip = IpPool.int_to_dotted(pool['range_start'] + 1)
            dns_ip = IpPool.int_to_dotted(pool['range_start'] + 2)

            open('/tmp/Corefile', 'w').write('. {\n    log\n    errors\n    auto\n    hosts /etc/coredns/hosts {\n        ttl 10\n    }\n}')
            hosts = [
                f'{lpos_ip}  {lpos_domain} www.{lpos_domain}',
                f'{lpos_ip}  www.msftconnecttest.com',
                '131.107.255.255  dns.msftncsi.com']
            if get_use_nlpt_sso():
                from urllib.parse import urlparse
                sso_domain = urlparse(docDB.get_setting('sso_login_url')).netloc
                hosts.append(f'{lpos_ip} {sso_domain}')
            open('/tmp/hosts', 'w').write('\n'.join(hosts))

            subprocess.call(f'{dcmd} run --rm --name copier-dns-{self["number"]} -v lpos-ipvlan{self["number"]}-dns:/app -d alpine sleep 3', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/Corefile copier-dns-{self["number"]}:/app/', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/hosts copier-dns-{self["number"]}:/app/', shell=True)
            start_cmd = list([
                f'{dcmd} run --rm --name lpos-ipvlan{self["number"]}-dns',
                f'--net=lpos-ipvlan{self["number"]} --ip={dns_ip}',
                f'-v lpos-ipvlan{self["number"]}-dns:/etc/coredns',
                '-d coredns/coredns:1.11.1 -conf /etc/coredns/Corefile'
            ])
            subprocess.call(' '.join(start_cmd), shell=True)
        return True

    def retreat_dns_server(self):
        if self['purpose'] in [0, 1, 3]:
            return True  # does not got a dns server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'

        try:
            subprocess.call(f'{dcmd} stop lpos-ipvlan{self["number"]}-dns', shell=True)
        except Exception:
            pass

        try:
            subprocess.call(f'{dcmd} volume rm lpos-ipvlan{self["number"]}-dns', shell=True)
        except Exception:
            pass

        return True

    def commit_dhcp_server(self):
        from elements import IpPool
        from helpers.system import check_integrity_vlan_dhcp_commit
        integrity = check_integrity_vlan_dhcp_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
            return True  # does not get a dhcp server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        if not 0 == subprocess.call(f'{dcmd} network ls | grep lpos-ipvlan{self["number"]}', shell=True):
            return False  # VLAN not defined, can't start DNS-Server

        # create ctrl-agent conf
        ctrl_agent_conf = dict({'http-host': '127.0.0.1', 'http-port': 8000})
        ctrl_agent_conf['control-sockets'] = {'dhcp4': {'socket-type': 'unix', 'socket-name': '/dev/null'}}
        ctrl_agent_conf['loggers'] = [{'name': 'kea-ctrl-agent', 'output_options': [{'output': 'stdout'}], 'severity': 'INFO'}]
        open('/tmp/kea-ctrl-agent.conf', 'w').write(json.dumps({'Control-agent': ctrl_agent_conf}, indent=4))

        # create dhcp4 conf
        dhcp4_conf = dict({'subnet4': list(), 'option-data': list()})
        dhcp4_conf['interfaces-config'] = {'interfaces': ['*'], 'service-sockets-max-retries': 5, 'service-sockets-require-all': True}
        dhcp4_conf['loggers'] = [{'name': 'kea-dhcp4', 'output_options': [{'output': 'stdout'}], 'severity': 'INFO'}]
        dhcp4_conf['lease-database'] = {'type': 'memfile', 'persist': True, 'name': '/tmp/kea-leases4.csv'}
        dhcp4_conf['authoritative'] = True
        if self['purpose'] == 0:
            # specialties for play vlan
            import re
            dhcp_ip = docDB.get_setting('play_dhcp')
            dhcp4_conf.update({'renew-timer': 3600, 'rebind-timer': 3600, 'valid-lifetime': 3600})
            dhcp4_conf['reservation-mode'] = 'global'
            dhcp4_conf['reservations'] = list()
            dhcp4_conf['option-data'].append({'name': 'domain-name-servers', 'data': docDB.get_setting('upstream_dns')})
            dhcp4_conf['option-data'].append({'name': 'routers', 'data': docDB.get_setting('play_gateway')})
            # iterate over all play-pools
            for pool in IpPool.get_by_vlan(self['_id']):
                # if pool is additional-pool, add it to the available ranges
                if docDB.search_one('Table', {'add_ip_pool_id': pool['_id']}) is not None:
                    subnet = f'{pool.subnet_ip(dotted=True)}/{pool["mask"]}'
                    range = f'{IpPool.int_to_dotted(pool["range_start"])}-{IpPool.int_to_dotted(pool["range_end"])}'
                    for e in dhcp4_conf['subnet4']:
                        if e['subnet'] == subnet:
                            e['pools'].append({'pool': range})
                    else:
                        dhcp4_conf['subnet4'].append({'subnet': subnet, 'pools': [{'pool': range}]})
                # add all fully onboarded devices to reservations
                for device in docDB.search_many('Device', {'ip_pool_id': pool['_id'], 'ip': {'$ne': None}}):
                    device_mac = ':'.join(re.findall('..', device['mac']))
                    device_ip = IpPool.int_to_dotted(device['ip'])
                    dhcp4_conf['reservations'].append({'hw-address': device_mac, 'ip-address': device_ip})
        else:
            # specialties for onboarding vlan
            pool = IpPool.get_by_vlan(self['_id'])
            if len(pool) == 0:
                return False  # no needed pool defined
            pool = pool[0]
            subnet = f'{pool.subnet_ip(dotted=True)}/{pool["mask"]}'
            range = f'{IpPool.int_to_dotted(pool["range_start"] + 4)}-{IpPool.int_to_dotted(pool["range_end"])}'
            lpos_ip = IpPool.int_to_dotted(pool['range_start'] + 1)
            dns_ip = IpPool.int_to_dotted(pool['range_start'] + 2)
            dhcp_ip = IpPool.int_to_dotted(pool['range_start'] + 3)
            lpos_domain = '.'.join([docDB.get_setting('subdomain'), docDB.get_setting('domain')])
            dhcp4_conf.update({'renew-timer': 10, 'rebind-timer': 20, 'valid-lifetime': 20})
            dhcp4_conf['lease-database']['lfc-interval'] = 60
            dhcp4_conf['subnet4'].append({'subnet': subnet, 'pools': [{'pool': range}]})
            dhcp4_conf['option-data'].append({'name': 'domain-name-servers', 'data': dns_ip})
            dhcp4_conf['option-data'].append({'name': 'routers', 'data': lpos_ip})
            dhcp4_conf['option-data'].append({'name': 'v4-captive-portal', 'data': f'http://{lpos_domain}/', 'always-send': True})
        open('/tmp/kea-dhcp4.conf', 'w').write(json.dumps({'Dhcp4': dhcp4_conf}, indent=4))

        # decide wether to start or reload the server
        if not 0 == subprocess.call(f'{dcmd} ps --format=\u007b\u007b.Names\u007d\u007d | grep lpos-ipvlan{self["number"]}-dhcp', shell=True):
            # copy confs into volume
            subprocess.call(f'{dcmd} run --rm --name copier-dhcp-{self["number"]} -v lpos-ipvlan{self["number"]}-dhcp:/app -d alpine sleep 3', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/kea-ctrl-agent.conf copier-dhcp-{self["number"]}:/app/', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/kea-dhcp4.conf copier-dhcp-{self["number"]}:/app/', shell=True)
            # start container with volume
            start_cmd = list([
                f'{dcmd} run --rm --name lpos-ipvlan{self["number"]}-dhcp',
                f'--net=lpos-ipvlan{self["number"]} --ip={dhcp_ip}',
                f'-v lpos-ipvlan{self["number"]}-dhcp:/etc/kea',
                '-d docker.cloudsmith.io/isc/docker/kea-dhcp4:2.5.7'
            ])
            subprocess.call(' '.join(start_cmd), shell=True)
        else:
            # copy confs into container (indirectly to the volume)
            subprocess.call(f'{dcmd} cp /tmp/kea-ctrl-agent.conf lpos-ipvlan{self["number"]}-dhcp:/etc/kea/', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/kea-dhcp4.conf lpos-ipvlan{self["number"]}-dhcp:/etc/kea/', shell=True)
            # let the server reload it's config
            r = subprocess.check_output(f'{dcmd} exec lpos-ipvlan{self["number"]}-dhcp ps -a | grep dhcp4', shell=True).decode('utf-8').strip().split()[0]
            subprocess.call(f'{dcmd} exec lpos-ipvlan{self["number"]}-dhcp kill -HUP {r}', shell=True)
        return True

    def retreat_dhcp_server(self):
        if self['purpose'] in [1, 3]:
            return True  # does not got a dhcp server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'

        try:
            subprocess.call(f'{dcmd} stop lpos-ipvlan{self["number"]}-dhcp', shell=True)
        except Exception:
            pass

        try:
            subprocess.call(f'{dcmd} volume rm lpos-ipvlan{self["number"]}-dhcp', shell=True)
        except Exception:
            pass

        return True
