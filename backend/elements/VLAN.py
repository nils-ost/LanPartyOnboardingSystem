import os
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

        # hook the first IP of corresponding pool to haproxy
        try:
            format = '\u007b\u007b.ID\u007d\u007d|\u007b\u007b.Image\u007d\u007d|\u007b\u007b.Names\u007d\u007d'
            hap_container = subprocess.check_output(f"sudo docker ps --format='{format}' | grep haproxy", shell=True).decode('utf-8').split('|')[0]
            tmp_cmd = f'{dcmd} network inspect lpos-ipvlan{self["number"]}'
            for k in json.loads(subprocess.check_output(tmp_cmd, shell=True).decode('utf-8').strip())[0]['Containers']:
                if k.startswith(hap_container):
                    break  # haproxy allready connected to this vlan, for-else is not executed
            else:
                hap_ip = '.'.join(str(o) for o in IpPool.int_to_octetts(pool['range_start']))
                subprocess.call(f'{dcmd} network connect --ip={hap_ip} lpos-ipvlan{self["number"]} {hap_container}', shell=True)
        except Exception:
            pass  # haproxy container not started or can't be found, skipping this step

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
        from helpers.system import check_integrity_vlan_dns_commit
        integrity = check_integrity_vlan_dns_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
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
            lpos_ip = '.'.join(str(o) for o in IpPool.int_to_octetts(pool['range_start']))
            dns_ip = '.'.join(str(o) for o in IpPool.int_to_octetts(pool['range_start'] + 1))

            open('/tmp/Corefile', 'w').write('. {\n    hosts /app/hosts\n}')
            open('/tmp/hosts', 'w').write(f'{lpos_ip}  {lpos_domain} www.{lpos_domain}')

            subprocess.call(f'{dcmd} run --rm --name copier-dns-{self["number"]} -v lpos-ipvlan{self["number"]}-dns:/app -d alpine sleep 3', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/Corefile copier-dns-{self["number"]}:/app/', shell=True)
            subprocess.call(f'{dcmd} cp /tmp/hosts copier-dns-{self["number"]}:/app/', shell=True)
            start_cmd = list([
                f'{dcmd} run --rm --name lpos-ipvlan{self["number"]}-dns',
                f'--net=lpos-ipvlan{self["number"]} --ip={dns_ip}',
                f'-v lpos-ipvlan{self["number"]}-dns:/app',
                'coredns/coredns -conf /app/Corefile'
            ])
            subprocess.call(' '.join(start_cmd), shell=True)
        return True

    def retreat_dns_server(self):
        if self['purpose'] in [1, 3]:
            return True  # does not get a dns server
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
        from helpers.system import check_integrity_vlan_dhcp_commit
        integrity = check_integrity_vlan_dhcp_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
            return True  # does not get a dns server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid
        
        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        
        # check lpos internal network exists
        # determine next free ip in lpos internal network
        internal_ip = '0.0.0.0'
        hap_ip = ''
        dns_ip = ''
        dhcp_ip = ''
        subnet_ip = ''
        subnet_mask = ''
        range_start = ''
        range_end = ''
        lpos_domain = ''
        # create ctrl-agent conf
        ctrl_agent_conf = dict({'http-host': internal_ip, 'http-port': 8000})
        ctrl_agent_conf['control-sockets'] = {'dhcp4': {'socket-type': 'unix', 'socket-name': '/run/kea/control_socket_4'}}
        ctrl_agent_conf['loggers'] = [{'name': 'kea-ctrl-agent', 'output_options': [{'output': 'stdout'}], 'severity': 'INFO'}]
        open('/tmp/kea-ctrl-agent.conf', 'w').write(json.dumps({'Control-agent': ctrl_agent_conf}, indent=4))
        # create dhcp4 conf
        dhcp4_conf = dict({'renew-timer': 2, 'rebind-timer': 5, 'valid-lifetime': 10, 'option-data': list()})
        dhcp4_conf['option-data'].append({'name': 'domain-name-servers', 'data': dns_ip})
        dhcp4_conf['option-data'].append({'name': 'routers', 'data': hap_ip})
        dhcp4_conf['option-data'].append({'name': 'v4-captive-portal', 'data': f'http://{lpos_domain}/', 'always-send': True})
        dhcp4_conf['subnet4'] = [{'id': 1, 'subnet': f'{subnet_ip}/{subnet_mask}', 'pools': [{'pool': f'{range_start}-{range_end}'}], 'interface': 'eth0'}]
        dhcp4_conf['interfaces-config'] = {'interfaces': ['eth0'], 'service-sockets-max-retries': 5, 'service-sockets-require-all': True}
        dhcp4_conf['control-socket'] = {'socket-type': 'unix', 'socket-name': '/run/kea/control_socket_4'}
        dhcp4_conf['loggers'] = [{'name': 'kea-dhcp4', 'output_options': [{'output': 'stdout'}], 'severity': 'INFO'}]
        dhcp4_conf['lease-database'] = {'type': 'memfile'}
        open('/tmp/kea-dhcp4.conf', 'w').write(json.dumps({'Dhcp4': dhcp4_conf}, indent=4))
        # copy confs into volume
        subprocess.call(f'{dcmd} run --rm --name copier-dhcp-{self["number"]} -v lpos-ipvlan{self["number"]}-dhcp:/app -d alpine sleep 3', shell=True)
        subprocess.call(f'{dcmd} cp /tmp/kea-ctrl-agent.conf copier-dhcp-{self["number"]}:/app/', shell=True)
        subprocess.call(f'{dcmd} cp /tmp/kea-dhcp4.conf copier-dhcp-{self["number"]}:/app/', shell=True)
        # start container with volume
        start_cmd = list([
            f'{dcmd} run --rm --name lpos-ipvlan{self["number"]}-dhcp',
            f'--net=lpos-internal -p 127.0.0.1:80{self["number"]}:8000',
            f'--net=lpos-ipvlan{self["number"]} --ip={dhcp_ip}',
            f'-v lpos-ipvlan{self["number"]}-dhcp:/etc/kea',
            'docker.cloudsmith.io/isc/docker/kea-dhcp4'
        ])
        subprocess.call(' '.join(start_cmd), shell=True)

    def commit_dnsmasq_config(self):
        from elements import IpPool
        from helpers.system import check_integrity_vlan_dnsmasq_commit
        integrity = check_integrity_vlan_dnsmasq_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
            return True  # does not get a dnsmasq config
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid
        iname = docDB.get_setting('os_nw_interface')
        iname = f'vlan{self["number"]}@{iname}'
        dnsmasq_path = docDB.get_setting('os_dnsmasq_path')
        domain = docDB.get_setting('domain')
        subdomain = docDB.get_setting('subdomain')
        upstream_dns = docDB.get_setting('upstream_dns')
        gateway = docDB.get_setting('play_gateway')
        fqdn = subdomain + '.' + domain

        # determine IP
        if self['purpose'] == 0:
            for pool in IpPool.get_by_vlan(self['_id']):
                if pool['lpos']:
                    break
            else:
                return False  # no pool defined as lpos
        else:
            pool = IpPool.get_by_vlan(self['_id'])
            if len(pool) == 0:
                return False  # no needed pool defined
            pool = pool[0]
        ip = '.'.join([str(e) for e in IpPool.int_to_octetts(pool['range_start'])])

        lines = list()

        # special lines for onboarding VLANs
        if self['purpose'] == 2:
            lines.append(f'host-record={fqdn},{ip},10')
            first_ip = '.'.join([str(o) for o in IpPool.int_to_octetts(pool['range_start'] + 1)])
            last_ip = '.'.join([str(o) for o in IpPool.int_to_octetts(pool['range_end'])])
            lines.append(f'dhcp-range={iname},{first_ip},{last_ip},{pool.mask_dotted()},10s')

        # special lines for play VLAN
        else:
            import re
            lines.append('localise-queries')
            lines.append('no-resolv')
            lines.append(f'host-record={fqdn},{ip}')
            lines.append(f'server={upstream_dns}')
            lines.append(f'local=/{domain}/')
            lines.append('bogus-priv')
            lines.append('domain-needed')
            lines.append(f'dhcp-option={iname},3,{gateway}')
            # determine all devices fully onboarded on play VLAN (or rather any play IpPool)
            for pool in IpPool.get_by_vlan(self['_id']):
                first_ip = '.'.join([str(o) for o in IpPool.int_to_octetts(pool['range_start'])])
                last_ip = '.'.join([str(o) for o in IpPool.int_to_octetts(pool['range_end'])])
                # check if pool is a seat-pool
                if docDB.search_one('Table', {'seat_ip_pool_id': pool['_id']}) is not None:
                    lines.append(f'dhcp-range={iname},{first_ip},static,{pool.mask_dotted()},1h')
                # check is pool is a additional-pool
                elif docDB.search_one('Table', {'add_ip_pool_id': pool['_id']}) is not None:
                    lines.append(f'dhcp-range={iname},{first_ip},{last_ip},{pool.mask_dotted()},1h')
                for device in docDB.search_many('Device', {'ip_pool_id': pool['_id'], 'ip': {'$ne': None}}):
                    device_mac = ':'.join(re.findall('..', device['mac']))
                    device_ip = '.'.join([str(e) for e in IpPool.int_to_octetts(device['ip'])])
                    lines.append(f'dhcp-host={device_mac},{device_ip},1h')

        # write config file
        with open(os.path.join(dnsmasq_path, f"vlan{self['number']}.config"), 'w') as f:
            f.write('\n'.join(lines))
        return True

    def retreat_dnsmasq_config(self):
        from helpers.system import check_integrity_vlan_dnsmasq_commit
        integrity = check_integrity_vlan_dnsmasq_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
            return True  # does not got a dnsmasq config
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid
        dnsmasq_path = docDB.get_setting('os_dnsmasq_path')
        try:
            os.remove(os.path.join(dnsmasq_path, f"vlan{self['number']}.config"))
        except FileNotFoundError:
            pass
        return True
