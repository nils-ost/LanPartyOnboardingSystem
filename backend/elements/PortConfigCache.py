from elements._elementBase import ElementBase, docDB


class PortConfigCache(ElementBase):
    _attrdef = dict(
        port_id=ElementBase.addAttr(notnone=True, fk='Port'),
        scope=ElementBase.addAttr(type=int, notnone=True),
        skip=ElementBase.addAttr(type=bool, default=False, notnone=True),
        isolate=ElementBase.addAttr(type=bool, default=False, notnone=True),
        vlan_ids=ElementBase.addAttr(type=list, default=list(), notnone=True),
        default_vlan_id=ElementBase.addAttr(default=None, fk='VLAN'),
        enabled=ElementBase.addAttr(type=bool, default=True, notnone=True),
        mode=ElementBase.addAttr(default='optional', notnone=True),
        receive=ElementBase.addAttr(default='any', notnone=True),
        force=ElementBase.addAttr(type=bool, default=False, notnone=True)
    )

    @classmethod
    def get_by_port(cls, port_id, scope=0):
        from_db = docDB.search_one(cls.__name__, {'port_id': port_id, 'scope': scope})
        if from_db is not None:
            return cls(from_db)
        g = cls({'port_id': port_id, 'scope': scope})
        g._generate()
        return g

    @classmethod
    def delete_by_port(cls, port_id):
        docDB.delete_many(cls.__name__, {'port_id': port_id})

    def _generate(self):
        from elements import Port, VLAN, Switch, Device
        from helpers.switchmgmt import switch_restart_order

        self['skip'] = False
        self['isolate'] = False
        self['vlan_ids'] = list()
        self['default_vlan_id'] = None
        self['enabled'] = True
        self['mode'] = 'strict'
        self['receive'] = 'only untagged'
        self['force'] = False
        manual_config = self.port()['commit_config'] if self['scope'] == 0 else self.port()['retreat_config']
        manual_disabled = self.port()['commit_disabled'] if self['scope'] == 0 else self.port()['retreat_disabled']

        if self.port() == Port.get_lpos():
            # Add mgmt-VLAN
            for vlan in VLAN.get_by_purpose(1):
                self['vlan_ids'].append(vlan['_id'])
                self['default_vlan_id'] = vlan['_id']
            # Add play-VLAN
            for vlan in VLAN.get_by_purpose(0):
                self['vlan_ids'].append(vlan['_id'])
            # Add all onboarding-VLANs
            for sw in Switch.all():
                if sw['onboarding_vlan_id'] is not None:
                    self['vlan_ids'].append(sw['onboarding_vlan_id'])
            # set receive mode to any
            self['receive'] = 'any'
        elif self.port()['switchlink']:
            # Add mgmt-VLAN
            for vlan in VLAN.get_by_purpose(1):
                self['vlan_ids'].append(vlan['_id'])
            # Add play-VLAN
            for vlan in VLAN.get_by_purpose(0):
                self['vlan_ids'].append(vlan['_id'])
                self['default_vlan_id'] = vlan['_id']
            # Add subsequent onboading-VLANs
            try:
                for switch_id in switch_restart_order(self.port().switchlink_port().switch()):
                    sw = Switch.get(switch_id)
                    if sw['onboarding_vlan_id'] is not None:
                        self['vlan_ids'].append(sw['onboarding_vlan_id'])
            except Exception:
                pass
            # Add other-VLANs if present
            if manual_config is not None and 'other_vlans' in manual_config:
                for vlan_id in manual_config['other_vlans']:
                    self['vlan_ids'].append(vlan_id)
            # set receive mode to only tagged
            self['receive'] = 'only tagged'
        elif manual_disabled:
            # mark disabled Ports to be skipped
            self['skip'] = True
        elif manual_config is not None:
            # apply manual Port configuration
            self['vlan_ids'] = manual_config['vlans']
            self['default_vlan_id'] = manual_config['default']
            self['enabled'] = manual_config['enabled']
            self['mode'] = manual_config['mode']
            self['receive'] = manual_config['receive']
            self['force'] = manual_config['force']
        elif self.port()['onboarding_vlan_id'] is None:
            # Port is part of a core Switch, all not switchlinks get the play-VLAN
            for vlan in VLAN.get_by_purpose(0):
                self['vlan_ids'].append(vlan['_id'])
                self['default_vlan_id'] = vlan['_id']
        elif not self.port()['participants']:
            # Port is not designated to particiants, get play-VLAN but not onboarding-VLAN
            for vlan in VLAN.get_by_purpose(0):
                self['vlan_ids'].append(vlan['_id'])
                self['default_vlan_id'] = vlan['_id']
        else:
            # participant Port
            for device in Device.get_by_port(self['port_id']):
                if device['ip'] is not None:
                    # a valid configured Device is connected to this Port, therefor give is access to play-VLAN
                    for vlan in VLAN.get_by_purpose(0):
                        self['vlan_ids'].append(vlan['_id'])
                        self['default_vlan_id'] = vlan['_id']
                    break
            else:
                # no configured Device on this Port, connect it to the onboarding-VLAN
                try:
                    self['default_vlan_id'] = self.port().switch()['onboarding_vlan_id']
                    self['vlan_ids'].append(self['default_vlan_id'])
                    self['isolate'] = True
                except Exception:
                    pass
        self.save()
