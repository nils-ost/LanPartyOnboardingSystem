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
        retreat_disabled=ElementBase.addAttr(type=bool, default=False, notnone=True),
        commit_config=ElementBase.addAttr(type=dict, default=None),
        retreat_config=ElementBase.addAttr(type=dict, default=None)
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
        if self['switchlink']:
            self['commit_config'] = None
            self['retreat_config'] = None
            self['commit_disabled'] = False
            self['retreat_disabled'] = False
        if self['commit_config'] is not None:
            # enabled
            if 'enabled' not in self['commit_config'] or self['commit_config']['enabled'] is None:
                self['commit_config']['enabled'] = True
            if not isinstance(self['commit_config']['enabled'], bool):
                errors['commit_config.enabled'] = {'code': 3, 'desc': 'needs to be of type bool'}
            # force
            if 'force' not in self['commit_config'] or self['commit_config']['force'] is None:
                self['commit_config']['force'] = False
            if not isinstance(self['commit_config']['force'], bool):
                errors['commit_config.force'] = {'code': 3, 'desc': 'needs to be of type bool'}
            # mode
            if 'mode' not in self['commit_config'] or self['commit_config']['mode'] is None:
                self['commit_config']['mode'] = '0x01'
            if not isinstance(self['commit_config']['mode'], str):
                errors['commit_config.mode'] = {'code': 3, 'desc': 'needs to be of type str'}
            elif self['commit_config']['mode'] not in ['0x00', '0x01', '0x02', '0x03']:
                valid_values = '0x00 (disabled), 0x01 (optional), 0x02 (enabled), 0x03 (strict)'
                errors['commit_config.mode'] = {'code': 94, 'desc': f"needs to be one of {valid_values} but is {self['commit_config']['mode']}"}
            # receive
            if 'receive' not in self['commit_config'] or self['commit_config']['receive'] is None:
                self['commit_config']['receive'] = '0x00'
            if not isinstance(self['commit_config']['receive'], str):
                errors['commit_config.receive'] = {'code': 3, 'desc': 'needs to be of type str'}
            elif self['commit_config']['receive'] not in ['0x00', '0x01', '0x02']:
                valid_values = '0x00 (any), 0x01 (only tagged), 0x02 (only untagged)'
                errors['commit_config.receive'] = {'code': 94, 'desc': f"needs to be one of {valid_values} but is {self['commit_config']['receive']}"}
            # vlans
            if len(self['commit_config']['vlans']) == 0:
                errors['commit_config.vlans'] = {'code': 95, 'desc': 'at least one vlan is required'}
            else:
                for vlan_id in self['commit_config']['vlans']:
                    if docDB.get('VLAN', vlan_id) is None:
                        errors['commit_config.vlans'] = {'code': 90, 'desc': f"There is no VLAN with id '{vlan_id}'"}
                        break
                else:
                    # deault (vlan)
                    if 'deault' not in self['commit_config'] or self['commit_config']['deault'] is None:
                        self['commit_config']['deault'] = self['commit_config']['vlans'][0]
                    if docDB.get('VLAN', self['commit_config']['deault']) is None:
                        errors['commit_config.vlans'] = {'code': 90, 'desc': f"There is no VLAN with id '{self['commit_config']['deault']}'"}
        if self['retreat_config'] is not None:
            # enabled
            if 'enabled' not in self['retreat_config'] or self['retreat_config']['enabled'] is None:
                self['retreat_config']['enabled'] = True
            if not isinstance(self['retreat_config']['enabled'], bool):
                errors['retreat_config.enabled'] = {'code': 3, 'desc': 'needs to be of type bool'}
            # force
            if 'force' not in self['retreat_config'] or self['retreat_config']['force'] is None:
                self['retreat_config']['force'] = False
            if not isinstance(self['retreat_config']['force'], bool):
                errors['retreat_config.force'] = {'code': 3, 'desc': 'needs to be of type bool'}
            # mode
            if 'mode' not in self['retreat_config'] or self['retreat_config']['mode'] is None:
                self['retreat_config']['mode'] = '0x01'
            if not isinstance(self['retreat_config']['mode'], str):
                errors['retreat_config.mode'] = {'code': 3, 'desc': 'needs to be of type str'}
            elif self['retreat_config']['mode'] not in ['0x00', '0x01', '0x02', '0x03']:
                valid_values = '0x00 (disabled), 0x01 (optional), 0x02 (enabled), 0x03 (strict)'
                errors['retreat_config.mode'] = {'code': 94, 'desc': f"needs to be one of {valid_values} but is {self['retreat_config']['mode']}"}
            # receive
            if 'receive' not in self['retreat_config'] or self['retreat_config']['receive'] is None:
                self['retreat_config']['receive'] = '0x00'
            if not isinstance(self['retreat_config']['receive'], str):
                errors['retreat_config.receive'] = {'code': 3, 'desc': 'needs to be of type str'}
            elif self['retreat_config']['receive'] not in ['0x00', '0x01', '0x02']:
                valid_values = '0x00 (any), 0x01 (only tagged), 0x02 (only untagged)'
                errors['retreat_config.receive'] = {'code': 94, 'desc': f"needs to be one of {valid_values} but is {self['retreat_config']['receive']}"}
            # vlans
            if len(self['retreat_config']['vlans']) == 0:
                errors['retreat_config.vlans'] = {'code': 95, 'desc': 'at least one vlan is required'}
            else:
                for vlan_id in self['retreat_config']['vlans']:
                    if docDB.get('VLAN', vlan_id) is None:
                        errors['retreat_config.vlans'] = {'code': 90, 'desc': f"There is no VLAN with id '{vlan_id}'"}
                        break
                else:
                    # deault (vlan)
                    if 'deault' not in self['retreat_config'] or self['retreat_config']['deault'] is None:
                        self['retreat_config']['deault'] = self['retreat_config']['vlans'][0]
                    if docDB.get('VLAN', self['retreat_config']['deault']) is None:
                        errors['retreat_config.vlans'] = {'code': 90, 'desc': f"There is no VLAN with id '{self['retreat_config']['deault']}'"}
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
