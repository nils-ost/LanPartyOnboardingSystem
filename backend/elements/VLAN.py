import os
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

        iname = docDB.get_setting('os_nw_interface')
        netplan_path = docDB.get_setting('os_netplan_path')
        route_cfg = ''

        if self['purpose'] == 0:
            def_gw = docDB.get_setting('play_gateway')
            def_ns = docDB.get_setting('upstream_dns')
            route_cfg = f"""
      gateway4: {def_gw}
      nameservers:
        addresses: [{def_ns}]"""
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
        mask = pool['mask']
        cfg = f"""network:
  version: 2
  renderer: networkd
  vlans:
    vlan{self['number']}:
      id: {self['number']}
      link: {iname}
      addresses:
        - {ip}/{mask}
      dhcp4: no{route_cfg}"""
        with open(os.path.join(netplan_path, f"02-vlan{self['number']}.yaml"), 'w') as f:
            f.write(cfg)
        return True

    def retreat_os_interface(self):
        from helpers.system import check_integrity_vlan_interface_commit
        integrity = check_integrity_vlan_interface_commit()
        if not integrity.get('code', 1) == 0:
            return False  # integrity check failed, can't continue

        if self['purpose'] == 3:
            return True  # does not got an interface
        if self['_id'] is None:
            return False  # not saved yet, therefor could be invalid
        netplan_path = docDB.get_setting('os_netplan_path')
        try:
            os.remove(os.path.join(netplan_path, f"02-vlan{self['number']}.yaml"))
        except FileNotFoundError:
            pass
        return True

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
