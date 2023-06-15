import cherrypy
from elements._elementBase import ElementBase, docDB
from MTSwitch import MikroTikSwitch

switch_objects = dict()
switch_macs = list()


class Switch(ElementBase):
    _attrdef = dict(
        addr=ElementBase.addAttr(unique=True, notnone=True),
        user=ElementBase.addAttr(default='', notnone=True),
        pw=ElementBase.addAttr(default='', notnone=True),
        purpose=ElementBase.addAttr(type=int, default=0, notnone=True),
        onboarding_vlan_id=ElementBase.addAttr(default=None, fk='VLAN')
    )

    def validate(self):
        errors = dict()
        if self['purpose'] not in range(3):
            errors['purpose'] = {'code': 20, 'desc': 'needs to be 0, 1 or 2'}
        if self['purpose'] in range(1, 3):
            if self['onboarding_vlan_id'] is None:
                errors['onboarding_vlan_id'] = {'code': 21, 'desc': "can't be None for purposes 1 and 2"}
            else:
                v = docDB.get('VLAN', self['onboarding_vlan_id'])
                if v is None:
                    errors['onboarding_vlan_id'] = {'code': 22, 'desc': f"There is no VLAN with id '{self['onboarding_vlan_id']}'"}
                elif not v['purpose'] == 2:
                    errors['onboarding_vlan_id'] = {'code': 23, 'desc': f"VLAN purpose needs to be 2 (onboarding) but is '{v['purpose']}'"}
                elif docDB.search_one(self.__class__.__name__, {'onboarding_vlan_id': self['onboarding_vlan_id'], '_id': {'$ne': self['_id']}}) is not None:
                    errors['onboarding_vlan_id'] = {'code': 24, 'desc': 'This VLAN is allready used on a switch as onboarding_vlan'}
        return errors

    def save_pre(self):
        if self['purpose'] == 0:
            self['onboarding_vlan_id'] = None

    def save_post(self):
        global switch_objects
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if not test_suite:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        self.scan_vlans()
        if self.scan_ports() == 0:
            from elements import Port
            for p in docDB.search_many('Port', {'switch_id': self['_id']}):
                port = Port(p)
                port.save()

    def delete_pre(self):
        if docDB.search_one('Table', {'switch_id': self['_id']}) is not None:
            return {'error': {'code': 2, 'desc': 'at least one Table is using this Switch'}}

    def delete_post(self):
        from elements import Port
        for p in [Port(p) for p in docDB.search_many('Port', {'switch_id': self['_id']})]:
            p.delete()

    def connected(self):
        global switch_objects
        global switch_macs
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:
            return False
        if not self['_id']:
            return False
        if self['_id'] not in switch_objects:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        if not switch_objects[self['_id']].connected:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        swi = switch_objects[self['_id']]
        if swi.connected and swi.mac_addr not in switch_macs:
            switch_macs.append(swi.mac_addr)
        return swi.connected

    def mac_addr(self):
        global switch_objects
        if not self.connected():
            return ''
        return switch_objects[self['_id']].mac_addr

    def scan_devices(self):
        global switch_objects
        global switch_macs
        from elements import Device, Port
        if not self.connected():
            return 0
        new_count = 0
        swi = switch_objects[self['_id']]
        swi.reloadHosts()
        for port in swi.ports:
            p = Port.get_by_number(self['_id'], port.idx)
            if p is None:
                continue
            switchlink = False
            for host in port.hosts:
                if host in switch_macs:
                    switchlink = True
                    continue  # this host is a switch, switches are not handled here
                device = Device.get_by_mac(host)
                if device is None and not p['switchlink']:
                    device = Device({'mac': host, 'port_id': p['_id']})
                    device.save()
                    new_count += 1
                elif device is None:
                    # skip as this is a switchlink port and regular devices are not connected on switchlink ports
                    pass
                elif p['switchlink'] and device.port() is not None and device.port() == p:
                    # remove the port from this device as the current port is a switchlink port, those do not connect devices
                    device['port_id'] = None
                    device.save()
                elif not p['switchlink'] and device.port() is not None and not device.port() == p:
                    other_port = device.port()
                    try:
                        other_port = switch_objects[other_port['switch_id']].ports[other_port['number']]
                        if host not in other_port.hosts or len(port.hosts) <= len(other_port.hosts):
                            device.port(p)
                            device.save()
                    except Exception:
                        pass
            if not switchlink == p['switchlink']:
                p['switchlink'] = switchlink
                p.save()
        return new_count

    def scanned_port_hosts(self, port_idx):
        """
        returns a list of mac addresses that are currently recognized on the switch-port
        """
        global switch_objects
        if not self.connected():
            return []
        swi = switch_objects[self['_id']]
        return swi.ports[port_idx].hosts

    def scan_vlans(self):
        global switch_objects
        from elements import VLAN
        if not self.connected():
            return 0
        new_count = 0
        swi = switch_objects[self['_id']]
        swi.reloadVlans()
        for vlan in swi.vlans:
            v = VLAN.get_by_number(vlan.id)
            if v is None:
                v = VLAN({'number': vlan.id, 'purpose': 3})
                v.save()
                new_count += 1
        return new_count

    def scan_ports(self):
        global switch_objects
        from elements import Port
        if not self.connected():
            return 0
        new_count = 0
        swi = switch_objects[self['_id']]
        swi.reloadVlans()
        for port in swi.ports:
            p = Port.get_by_number(self['_id'], port.idx)
            if p is None:
                p = Port({'number': port.idx, 'switch_id': self['_id']})
                p.save()
                new_count += 1
        return new_count

    def known_vlans(self):
        global switch_objects
        from elements import VLAN
        result = list()
        self.scan_vlans()
        if not self.connected():
            return result
        swi = switch_objects[self['_id']]
        for vlan in swi.vlans:
            v = VLAN.get_by_number(vlan.id)
            result.append(v['_id'])
        return result

    def add_vlan(self, vlan_id):
        global switch_objects
        from elements import VLAN
        if not self.connected():
            return 1
        vlan = VLAN.get(vlan_id)
        if vlan.get('_id') is None:
            return 2
        swi = switch_objects[self['_id']]
        swi.vlanAdd(vlan['number'])
        swi.commitNeeded()
        return 0

    def remove_vlan(self, vlan_id):
        global switch_objects
        from elements import VLAN
        if not self.connected():
            return 1
        vlan = VLAN.get(vlan_id)
        if vlan.get('_id') is None:
            return 2
        swi = switch_objects[self['_id']]
        swi.vlanRemove(vlan['number'])
        swi.commitNeeded()
        return 0

    def retreat(self):
        """
        Removes all configuration eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        global switch_objects
        if not self.connected():
            return
        swi = switch_objects[self['_id']]
        swi.setMgmtVlan(None)
        for port in swi.ports:
            missing_fwd = list()
            swi.portEdit(port, enabled=True, vmode='optional', vreceive='any', vdefault=1, vforce=False)
            for idx in range(len(swi.ports)):
                if idx == port.idx:
                    continue
                if idx not in port._fwd:
                    missing_fwd.append(idx)
            for idx in missing_fwd:
                swi.portEdit(port, fwdTo=idx)
        vlan_ids = list()
        for vlan in swi.vlans:
            vlan_ids.append(vlan.id)
        for vlan_id in vlan_ids:
            swi.vlanRemove(vlan_id)
        swi.commitNeeded()
        swi.reloadAll()

    def commit(self):
        """
        Sends all required configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import VLAN, Port, Device
        if not self.connected():
            return
        swi = switch_objects[self['_id']]
        for vlan in VLAN.get_by_purpose(0):  # Add Play VLAN
            swi.vlanAddit(vlan=vlan['number'])
        mgmt_vlan_nb = 1
        for vlan in VLAN.get_by_purpose(1):  # Add Mgmt VLAN
            swi.vlanAddit(vlan=vlan['number'])
            mgmt_vlan_nb = vlan['number']

        for idx in range(len(swi.ports)):  # TODO: maybe rework later on
            port = Port.get_by_number(self['_id'], idx)
            if self['onboarding_vlan_id'] is not None:
                onboarding_vlan_nb = VLAN.get(self['onboarding_vlan_id'])['number']
                swi.vlanAddit(vlan=onboarding_vlan_nb)
                if not port['switchlink'] and len(Device.get_by_port(port['_id'])) == 0:
                    swi.portEdit(idx, vmode='strict', vreceive='only untagged', vdefault=onboarding_vlan_nb, vforce=True)
            if port['switchlink']:
                swi.portEdit(idx, vmode='optional', vreceive='only tagged', vdefault=mgmt_vlan_nb, vforce=False)
                for vlan in swi.vlans:
                    swi.vlanEdit(vlan, memberAdd=idx)
        swi.commitNeeded()
        swi.reloadAll()

    def json(self):
        result = super().json()
        result['connected'] = self.connected()
        result['mac'] = self.mac_addr()
        result['known_vlans'] = self.known_vlans()
        return result
