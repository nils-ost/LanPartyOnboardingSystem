from elements._elementBase import ElementBase, docDB


class Port(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        switch_id=ElementBase.addAttr(notnone=True, fk='Switch'),
        participants=ElementBase.addAttr(type=bool, default=False, notnone=True),
        switchlink=ElementBase.addAttr(type=bool, default=False, notnone=True),
        switchlink_port_id=ElementBase.addAttr(default=None, fk='Port'),
        commit_disabled=ElementBase.addAttr(type=bool, default=False, notnone=True),
        commit_config=ElementBase.addAttr(type=dict, default=None)  # contains the configuration for commit_disabled ports, collected by retreat
    )

    @classmethod
    def get_by_number(cls, switch_id, number):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'number': number, 'switch_id': switch_id})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_lpos(cls):
        """
        Returns the port LPOS is connected to (or None if not yet identified)
        """
        import psutil
        from elements import Device
        my_macs = list()
        for iname, conf in psutil.net_if_addrs().items():
            if iname == 'lo':
                continue
            for e in conf:
                if e.family.name == 'AF_PACKET':
                    my_macs.append(e.address.replace(':', ''))
        for mac in my_macs:
            d = Device.get_by_mac(mac)
            if d is not None and d['port_id'] is not None:
                return d.port()
        return None

    @classmethod
    def get_switchlinks(cls, switch_id=None):
        if switch_id is None:
            return [cls(p) for p in docDB.search_many(cls.__name__, {'switchlink': True})]
        else:
            return [cls(p) for p in docDB.search_many(cls.__name__, {'switchlink': True, 'switch_id': switch_id})]

    def validate(self):
        errors = dict()
        if docDB.get('Switch', self['switch_id']) is None:
            errors['switch_id'] = {'code': 90, 'desc': f"There is no Switch with id '{self['switch_id']}'"}
        if self['number'] < 0:
            errors['number'] = {'code': 91, 'desc': 'needs to be 0 or bigger'}
        elif docDB.search_one(self.__class__.__name__, {'switch_id': self['switch_id'], 'number': self['number'], '_id': {'$ne': self['_id']}}) is not None:
            errors['number'] = {'code': 92, 'desc': 'needs to be unique per Switch'}
        if self['switchlink_port_id'] is not None:
            fromdb = docDB.get('Port', self['switchlink_port_id'])
            if fromdb is None:
                errors['switchlink_port_id'] = {'code': 90, 'desc': f"There is no Port with id '{self['switchlink_port_id']}'"}
            elif not fromdb['switchlink']:
                errors['switchlink_port_id'] = {'code': 93, 'desc': f"The Port '{self['switchlink_port_id']}' is not declared as a switchlink"}
        return errors

    def save_pre(self):
        if self['_id'] is None:
            self._cache['switchlink_port_id_fromdb'] = None
        else:
            self._cache['switchlink_port_id_fromdb'] = docDB.get(self.__class__.__name__, self['_id'])['switchlink_port_id']
        if self['switchlink']:
            self['participants'] = False
        else:
            self['switchlink_port_id'] = None
            switch = docDB.get('Switch', self['switch_id'])
            if switch['purpose'] == 0:
                self['participants'] = False
            elif switch['purpose'] == 1:
                self['participants'] = True

    def save_post(self):
        if self._cache['switchlink_port_id_fromdb'] is not None and not self['switchlink_port_id'] == self._cache['switchlink_port_id_fromdb']:
            oslp = Port.get(self._cache['switchlink_port_id_fromdb'])
            if oslp['switchlink_port_id'] == self['_id']:
                oslp['switchlink_port_id'] = None
                oslp.save()
        slp = self.switchlink_port()
        if slp is not None and not slp['switchlink_port_id'] == self['_id']:
            slp['switchlink_port_id'] = self['_id']
            slp.save()
        if self._cache['switchlink_port_id_fromdb'] is not None and self['switchlink_port_id'] is None and self['switchlink']:
            self.switch().scan_devices()

    def delete_post(self):
        slp = self.switchlink_port()
        if slp is not None:
            slp['switchlink_port_id'] = None
            slp.save()

    def vlan_ids(self):
        from elements.Switch import switch_objects
        from elements import VLAN
        result = list()
        if self['switch_id'] not in switch_objects:
            return result
        sw = switch_objects[self['switch_id']]
        for v in sw.vlans:
            if self['number'] in v._member:
                result.append(VLAN.get_by_number(v.id)['_id'])
        return result

    def type(self):
        from elements.Switch import switch_objects
        if self['switch_id'] not in switch_objects:
            return ''
        sw = switch_objects[self['switch_id']]
        if self['number'] not in range(len(sw.ports)):
            return ''
        return sw.ports[self['number']].type

    def enabled(self):
        from elements.Switch import switch_objects
        if self['switch_id'] not in switch_objects:
            return False
        sw = switch_objects[self['switch_id']]
        if self['number'] not in range(len(sw.ports)):
            return False
        return sw.ports[self['number']].enabled

    def link(self):
        from elements.Switch import switch_objects
        if self['switch_id'] not in switch_objects:
            return False
        sw = switch_objects[self['switch_id']]
        if self['number'] not in range(len(sw.ports)):
            return False
        return sw.ports[self['number']].link

    def speed(self):
        from elements.Switch import switch_objects
        if self['switch_id'] not in switch_objects:
            return ''
        sw = switch_objects[self['switch_id']]
        if self['number'] not in range(len(sw.ports)):
            return ''
        return sw.ports[self['number']].speed

    def scanned_hosts(self):
        """
        returns a list of mac addresses that are currently recognized on this switch-port
        """
        return self.switch().scanned_port_hosts(self['number'])

    def json(self):
        result = super().json()
        result['vlan_ids'] = self.vlan_ids()
        result['type'] = self.type()
        result['enabled'] = self.enabled()
        result['link'] = self.link()
        result['speed'] = self.speed()
        return result
