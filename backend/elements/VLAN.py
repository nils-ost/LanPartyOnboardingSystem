import json
import docker
import tempfile
import tarfile
import pathlib
import os
from noapiframe import ElementBase, docDB


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

    def save_post(self):
        from elements import Port, PortConfigCache
        for p in Port.all():
            PortConfigCache.delete_by_port(p['_id'])

    def delete_pre(self):
        if docDB.search_one('IpPool', {'vlan_id': self['_id']}) is not None:
            return {'error': {'code': 1, 'desc': 'at least one IpPool is using this VLAN'}}
        if docDB.search_one('Switch', {'onboarding_vlan_id': self['_id']}) is not None:
            return {'error': {'code': 4, 'desc': 'at least one Switch is using this VLAN'}}
        from elements import Switch, Port
        for switch in Switch.all():
            switch.remove_vlan(self['number'])
        for port in Port.all():
            if port['commit_config'] is not None or port['retreat_config'] is not None:
                if port['commit_config'] is not None and 'vlans' in port['commit_config'] and self['_id'] in port['commit_config']['vlans']:
                    port['commit_config']['vlans'].remove(self['_id'])
                if port['commit_config'] is not None and 'other_vlans' in port['commit_config'] and self['_id'] in port['commit_config']['other_vlans']:
                    port['commit_config']['other_vlans'].remove(self['_id'])
                if port['retreat_config'] is not None and 'vlans' in port['retreat_config'] and self['_id'] in port['retreat_config']['vlans']:
                    port['retreat_config']['vlans'].remove(self['_id'])
                port.save()

    def delete_post():
        from elements import Port, PortConfigCache
        for p in Port.all():
            PortConfigCache.delete_by_port(p['_id'])

    def commit_os_interface(self):
        from elements import IpPool, Setting
        from helpers.system import check_integrity_vlan_interface_commit
        from helpers.haproxy import ssoHAproxy, lposHAproxy
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

        iname = Setting.value('os_nw_interface')
        dcli = docker.from_env()

        try:
            dcli.networks.get(f"lpos-ipvlan{self['number']}")
        except docker.errors.NotFound:
            # vlan not yet defined, defining it
            ipam_pool = docker.types.IPAMPool(subnet=f'{pool.subnet_ip(dotted=True)}/{pool["mask"]}')
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            dcli.networks.create(name=f"lpos-ipvlan{self['number']}", driver='ipvlan', ipam=ipam_config, options={'parent': f'{iname}.{self["number"]}'})

        # depending on the vlan-purpose configure haproxy(s)
        if self['purpose'] == 0:
            lposHAproxy.attach_ipvlan(f"lpos-ipvlan{self['number']}", Setting.value('play_ip'))
        else:
            lposHAproxy.attach_ipvlan(f"lpos-ipvlan{self['number']}", pool['range_start'] + 1)
            if Setting.value('nlpt_sso'):
                ssoHAproxy.attach_ipvlan(f"lpos-ipvlan{self['number']}", pool['range_start'] + 4)

        return True

    def retreat_os_interface(self):
        if self['purpose'] in [1, 3]:
            return True  # does not got an interface
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcli = docker.from_env()

        try:
            dnet = dcli.networks.get(f"lpos-ipvlan{self['number']}")
        except docker.errors.NotFound:
            return True  # allready removed

        # unbind vlan from all containers
        for dcon in dnet.containers:
            dnet.disconnect(dcon.id)

        dnet.remove()
        return True

    def commit_dns_server(self):
        from elements import Setting, IpPool
        from helpers.system import check_integrity_vlan_dns_commit
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

        dcli = docker.from_env()
        try:
            dnet = dcli.networks.get(f'lpos-ipvlan{self["number"]}')
        except docker.errors.NotFound:
            return False  # VLAN not defined, can't start DNS-Server

        create_con = False
        dcon = dcli.containers.list(filters={'name': f'lpos-ipvlan{self["number"]}-dns'})
        if len(dcon) == 0:
            create_con = True
        elif not dcon[0].status == 'running':
            dcon[0].stop()
            dcon[0].remove()
            create_con = True
        del dcon

        if create_con:
            # DNS-Server not yet started, configuring and starting it
            lpos_domain = '.'.join([Setting.value('subdomain'), Setting.value('domain')])
            lpos_ip = IpPool.int_to_dotted(pool['range_start'] + 1)
            dns_ip = IpPool.int_to_dotted(pool['range_start'] + 2)
            ssoproxy_ip = IpPool.int_to_dotted(pool['range_start'] + 4)

            # create a temporary container, to inject configuration to volume
            copier_con = dcli.containers.run(
                name=f'copier-dns-{self["number"]}',
                image='alpine',
                command='sleep 3',
                volumes=[f'lpos-ipvlan{self["number"]}-dns:/app:rw'],
                remove=True,
                detach=True
            )

            # place configuration into volume, using temporary container
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = pathlib.Path(temp_dir)

                with open(os.path.join(temp_path, 'Corefile'), 'w') as corefile:
                    corefile.write('. {\n    log\n    errors\n    auto\n    hosts /etc/coredns/hosts {\n        ttl 10\n    }\n}')

                with open(os.path.join(temp_path, 'hosts'), 'w') as hostsfile:
                    hosts = [
                        f'{lpos_ip}  {lpos_domain} www.{lpos_domain}',
                        f'{lpos_ip}  www.msftconnecttest.com',
                        '131.107.255.255  dns.msftncsi.com']
                    if Setting.value('nlpt_sso'):
                        from urllib.parse import urlparse
                        sso_domain = urlparse(Setting.value('sso_login_url')).netloc
                        hosts.append(f'{ssoproxy_ip} {sso_domain}')
                    hostsfile.write('\n'.join(hosts))

                with tempfile.TemporaryFile(suffix='.tar') as archive:
                    with tarfile.open(fileobj=archive, mode='w') as tar:
                        tar.add(os.path.join(temp_path, 'Corefile'), 'Corefile')
                        tar.add(os.path.join(temp_path, 'hosts'), 'hosts')
                    archive.flush()
                    archive.seek(0)

                    copier_con.put_archive('/app/', archive)

            # create, connect to VLAN and start container
            dcon = dcli.containers.create(
                name=f'lpos-ipvlan{self["number"]}-dns',
                image='coredns/coredns:1.11.1',
                command='-conf /etc/coredns/Corefile',
                volumes=[f'lpos-ipvlan{self["number"]}-dns:/etc/coredns:rw'],
                restart_policy={'Name': 'always'},
                detach=True
            )
            dnet.connect(dcon, ipv4_address=dns_ip)
            dcon.start()
        return True

    def retreat_dns_server(self):
        if self['purpose'] in [0, 1, 3]:
            return True  # does not got a dns server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcli = docker.from_env()

        try:
            dcon = dcli.containers.get(f'lpos-ipvlan{self["number"]}-dns')
            dcon.stop()
            dcon.remove()
        except Exception:
            pass

        try:
            dvol = dcli.volumes.get(f'lpos-ipvlan{self["number"]}-dns')
            dvol.remove()
        except Exception:
            pass

        return True

    def commit_dhcp_server(self):
        from elements import Setting, IpPool
        from helpers.system import check_integrity_vlan_dhcp_commit
        integrity = check_integrity_vlan_dhcp_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] in [1, 3]:
            return True  # does not get a dhcp server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcli = docker.from_env()
        try:
            dnet = dcli.networks.get(f'lpos-ipvlan{self["number"]}')
        except docker.errors.NotFound:
            return False  # VLAN not defined, can't start DHCP-Server

        # build ctrl-agent conf
        ctrl_agent_conf = dict({'http-host': '127.0.0.1', 'http-port': 8000})
        ctrl_agent_conf['control-sockets'] = {'dhcp4': {'socket-type': 'unix', 'socket-name': '/dev/null'}}
        ctrl_agent_conf['loggers'] = [{'name': 'kea-ctrl-agent', 'output_options': [{'output': 'stdout'}], 'severity': 'INFO'}]

        # build dhcp4 conf
        dhcp4_conf = dict({'subnet4': list(), 'option-data': list()})
        dhcp4_conf['interfaces-config'] = {'interfaces': ['*'], 'service-sockets-max-retries': 5, 'service-sockets-require-all': True}
        dhcp4_conf['loggers'] = [{'name': 'kea-dhcp4', 'output_options': [{'output': 'stdout'}], 'severity': 'INFO'}]
        dhcp4_conf['lease-database'] = {'type': 'memfile', 'persist': True, 'name': '/tmp/kea-leases4.csv'}
        dhcp4_conf['authoritative'] = True
        if self['purpose'] == 0:
            # specialties for play vlan
            import re
            dhcp_ip = Setting.value('play_dhcp')
            dhcp4_conf.update({'renew-timer': 1800, 'rebind-timer': 2700, 'valid-lifetime': 3600})
            dhcp4_conf['reservation-mode'] = 'global'
            dhcp4_conf['reservations'] = list()
            dhcp4_conf['option-data'].append({'name': 'domain-name-servers', 'data': Setting.value('upstream_dns')})
            dhcp4_conf['option-data'].append({'name': 'routers', 'data': Setting.value('play_gateway')})
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
            range = f'{IpPool.int_to_dotted(pool["range_start"] + 5)}-{IpPool.int_to_dotted(pool["range_end"])}'  # lpos, dns, dhcp, ssoproxy IPs substracted
            lpos_ip = IpPool.int_to_dotted(pool['range_start'] + 1)
            dns_ip = IpPool.int_to_dotted(pool['range_start'] + 2)
            dhcp_ip = IpPool.int_to_dotted(pool['range_start'] + 3)
            lpos_domain = '.'.join([Setting.value('subdomain'), Setting.value('domain')])
            dhcp4_conf.update({'renew-timer': 10, 'rebind-timer': 20, 'valid-lifetime': 30})
            dhcp4_conf['lease-database']['lfc-interval'] = 60
            dhcp4_conf['subnet4'].append({'subnet': subnet, 'pools': [{'pool': range}]})
            dhcp4_conf['option-data'].append({'name': 'domain-name-servers', 'data': dns_ip})
            dhcp4_conf['option-data'].append({'name': 'routers', 'data': lpos_ip})
            dhcp4_conf['option-data'].append({'name': 'v4-captive-portal', 'data': f'http://{lpos_domain}/', 'always-send': True})

        # create a temporary container, to inject configuration to volume
        copier_con = dcli.containers.run(
            name=f'copier-dhcp-{self["number"]}',
            image='alpine',
            command='sleep 3',
            volumes=[f'lpos-ipvlan{self["number"]}-dhcp:/app:rw'],
            remove=True,
            detach=True
        )

        # place configuration into volume, using temporary container
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            with open(os.path.join(temp_path, 'kea-ctrl-agent.conf'), 'w') as ctrlfile:
                ctrlfile.write(json.dumps({'Control-agent': ctrl_agent_conf}, indent=4))

            with open(os.path.join(temp_path, 'kea-dhcp4.conf'), 'w') as dhcpfile:
                dhcpfile.write(json.dumps({'Dhcp4': dhcp4_conf}, indent=4))

            with tempfile.TemporaryFile(suffix='.tar') as archive:
                with tarfile.open(fileobj=archive, mode='w') as tar:
                    tar.add(os.path.join(temp_path, 'kea-ctrl-agent.conf'), 'kea-ctrl-agent.conf')
                    tar.add(os.path.join(temp_path, 'kea-dhcp4.conf'), 'kea-dhcp4.conf')
                archive.flush()
                archive.seek(0)

                copier_con.put_archive('/app/', archive)

        # decide wether to start or reload the server
        start_con = False
        dcon = dcli.containers.list(filters={'name': f'lpos-ipvlan{self["number"]}-dhcp'})
        if len(dcon) == 0:
            start_con = True
        elif not dcon[0].status == 'running':
            dcon[0].stop()
            dcon[0].remove()
            start_con = True
        else:
            dcon = dcon[0]

        if start_con:
            # create, connect to VLAN and start container
            dcon = dcli.containers.create(
                name=f'lpos-ipvlan{self["number"]}-dhcp',
                image='docker.cloudsmith.io/isc/docker/kea-dhcp4:2.5.7',
                volumes=[f'lpos-ipvlan{self["number"]}-dhcp:/etc/kea:rw'],
                restart_policy={'Name': 'always'},
                detach=True
            )
            dnet.connect(dcon, ipv4_address=dhcp_ip)
            dcon.start()
        else:
            # let the server reload it's config
            r = dcon.exec_run('ps -a | grep dhcp4').output.decode('utf-8').strip().split()[0]
            dcon.exec_run(f'kill -HUP {r}')
        return True

    def retreat_dhcp_server(self):
        if self['purpose'] in [1, 3]:
            return True  # does not got a dhcp server
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid

        dcli = docker.from_env()

        try:
            dcon = dcli.containers.get(f'lpos-ipvlan{self["number"]}-dhcp')
            dcon.stop()
            dcon.remove()
        except Exception:
            pass

        try:
            dvol = dcli.volumes.get(f'lpos-ipvlan{self["number"]}-dhcp')
            dvol.remove()
        except Exception:
            pass

        return True
