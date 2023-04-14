import cherrypy
from elements._elementBase import ElementBase, docDB
from MTSwitch import MikroTikSwitch

switch_objects = dict()


class Switch(ElementBase):
    _attrdef = dict(
        addr=ElementBase.addAttr(unique=True, notnone=True),
        user=ElementBase.addAttr(default='', notnone=True),
        pw=ElementBase.addAttr(default='', notnone=True),
        purpose=ElementBase.addAttr(type=int, default=0, notnone=True),
        onboarding_vlan_id=ElementBase.addAttr(default=None)
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
        self.scan_ports()

    def delete_pre(self):
        if docDB.search_one('Table', {'switch_id': self['_id']}) is not None:
            return {'error': {'code': 2, 'desc': 'at least one Table is using this Switch'}}

    def delete_post(self):
        from elements import Port
        for p in [Port(p) for p in docDB.search_many('Port', {'switch_id': self['_id']})]:
            p.delete()

    def connected(self):
        global switch_objects
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if test_suite:
            return False
        if not self['_id']:
            return False
        if self['_id'] not in switch_objects:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        if not switch_objects[self['_id']].connected:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        return switch_objects[self['_id']].connected

    def mac_addr(self):
        global switch_objects
        if not self.connected():
            return ''
        return switch_objects[self['_id']].mac_addr

    def scan_devices(self):
        global switch_objects
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
            for host in port.hosts:
                device = Device.get_by_mac(host)
                if device is None:
                    device = Device({'mac': host, 'port_id': p['_id']})
                    device.save()
                    new_count += 1
                elif not device['port_id'] == p['_id']:
                    sw = Switch.get(p['switch_id'])
                    if sw.mac_addr() not in port.hosts:
                        device['port_id'] = p['_id']
                        device.save()
        return new_count

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

    def json(self):
        result = super().json()
        result['connected'] = self.connected()
        result['mac'] = self.mac_addr()
        result['known_vlans'] = self.known_vlans()
        return result
