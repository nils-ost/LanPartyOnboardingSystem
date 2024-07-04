from elements._elementBase import ElementBase, docDB


class PortConfigCache(ElementBase):
    _attrdef = dict(
        port_id=ElementBase.addAttr(notnone=True, fk='Port'),
        scope=ElementBase.addAttr(type=int, notnone=True),
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

        def take_manual_config(pcc, manual_config):
            pcc['vlan_ids'] = manual_config['vlans']
            pcc['default_vlan_id'] = manual_config['default']
            pcc['enabled'] = manual_config['enabled']
            pcc['mode'] = manual_config['mode']
            pcc['receive'] = manual_config['receive']
            pcc['force'] = manual_config['force']

        def take_current_config(pcc):
            from elements.Switch import switch_objects
            swi = switch_objects.get(pcc.port()['switch_id'], None)
            if swi is None:
                return
            if not swi.connected:
                return
            swi_port = swi.ports[pcc.port()['number']]
            pcc['enabled'] = swi_port.enabled
            pcc['mode'] = swi_port.vlan_mode
            pcc['receive'] = swi_port.vlan_receive
            pcc['force'] = swi_port.vlan_force
            pcc['default_vlan_id'] = VLAN.get_by_number(swi_port.vlan_default)
            if pcc['default_vlan_id'] is not None:
                pcc['default_vlan_id'] = pcc['default_vlan_id']['_id']
            for swi_vlan in swi.vlans:
                if swi_port.idx in swi_vlan._member:
                    v = VLAN.get_by_number(swi_vlan.id)
                    if v is not None:
                        pcc['vlan_ids'].append(v['_id'])

        device_config = None
        self['isolate'] = False
        self['vlan_ids'] = list()
        self['default_vlan_id'] = None
        self['enabled'] = True
        self['force'] = False
        if self['scope'] == 0:
            self['mode'] = 'strict'
            self['receive'] = 'only untagged'
            manual_config = self.port()['commit_config']
            manual_disabled = self.port()['commit_disabled']
            devices = Device.get_by_port(self['port_id'])
            if len(devices) == 1:
                device_config = devices[0]['commit_config']
        else:
            self['mode'] = 'optional'
            self['receive'] = 'any'
            manual_config = self.port()['retreat_config']
            manual_disabled = self.port()['retreat_disabled']
            devices = Device.get_by_port(self['port_id'])
            if len(devices) == 1:
                device_config = devices[0]['retreat_config']

        if self['scope'] == 0:
            # commit scope
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
                    for switch_id in switch_restart_order(self.port().switch()):
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
            elif device_config:
                # manual config on Device overwrites config of Port
                take_manual_config(self, device_config)
            elif manual_disabled:
                # take the current switch-port config for disabled port, to keep the config
                take_current_config(self)
            elif manual_config is not None:
                # apply manual Port configuration
                take_manual_config(self, manual_config)
            elif self.port().switch()['onboarding_vlan_id'] is None:
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

        else:
            # retreat scope
            if device_config:
                # manual config on Device overwrites config of Port
                take_manual_config(self, device_config)
            elif manual_disabled:
                # take the current switch-port config for disabled port, to keep the config
                take_current_config(self)
            elif manual_config is not None:
                # apply manual Port configuration
                take_manual_config(self, manual_config)
            else:
                default_vlan = VLAN.get_by_number(1)
                if default_vlan is None:
                    default_vlan = VLAN({'number': 1, 'purpose': 3, 'desc': 'default'})
                    default_vlan.save()
                self['vlan_ids'].append(default_vlan['_id'])
                self['default_vlan_id'] = default_vlan['_id']
        self.save()
