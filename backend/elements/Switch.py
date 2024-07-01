import cherrypy
from datetime import datetime
from elements._elementBase import ElementBase, docDB
from MTSwitch import MikroTikSwitch

switch_objects = dict()
switch_macs = list()


class Switch(ElementBase):
    _attrdef = dict(
        desc=ElementBase.addAttr(default='', notnone=True),
        addr=ElementBase.addAttr(unique=True, notnone=True),
        user=ElementBase.addAttr(default='', notnone=True),
        pw=ElementBase.addAttr(default='', notnone=True),
        purpose=ElementBase.addAttr(type=int, default=0, notnone=True),
        commited=ElementBase.addAttr(type=bool, default=False, notnone=True),
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
        from elements import Port
        global switch_objects
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if not test_suite:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        self.scan_vlans()
        self.scan_ports()
        for p in docDB.search_many('Port', {'switch_id': self['_id']}):
            port = Port(p)
            port.save()  # also automatically deletes corresponding PortConfigCache

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
        swi.reloadPorts()
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
                    new_count += 1
                elif device is None:
                    # skip as this is a switchlink port and regular devices are not connected on switchlink ports
                    pass
                elif p['switchlink'] and device['port_id'] is not None and device.port() == p:
                    # remove the port from this device as the current port is a switchlink port, those do not connect devices
                    device['port_id'] = None
                elif not p['switchlink'] and device['port_id'] is None:
                    device.port(p)
                elif not p['switchlink'] and device['port_id'] is not None and not device.port() == p:
                    other_port = device.port()
                    try:
                        other_port = switch_objects[other_port['switch_id']].ports[other_port['number']]
                        if host not in other_port.hosts or len(port.hosts) <= len(other_port.hosts):
                            device.port(p)
                    except Exception:
                        pass
                if device is not None:
                    device['last_scan_ts'] = int(datetime.now().timestamp())
                    device.save()  # generic save for everything happend above
            if not switchlink == p['switchlink'] and p['switchlink_port_id'] is None:
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

    def port_disable(self, port_number):
        global switch_objects
        if not self.connected():
            return 1
        swi = switch_objects[self['_id']]
        swi.portEdit(port_number, enabled=False)
        swi.commitNeeded()

    def port_enable(self, port_number):
        global switch_objects
        if not self.connected():
            return 1
        swi = switch_objects[self['_id']]
        swi.portEdit(port_number, enabled=True)
        swi.commitNeeded()

    def metrics(self):
        global switch_objects
        if not self.connected():
            return dict()
        swi = switch_objects[self['_id']]
        return swi.loadStatsRaw()

    def _retreat_vlans(self):
        """
        Removes all configured VLANs eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        from elements import VLAN, Port
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]
        swi.setMgmtVlan(None)

        # determine all VLANs needed by manual port commit configs
        manual_vlans = list()
        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            if port['retreat_disabled']:
                # keep all currently configured VLAN(membership)s
                for vlan_swi in swi.vlans:
                    if idx in vlan_swi._member:
                        manual_vlans.append(vlan_swi.id)
            elif port['retreat_config'] is not None:
                # keep all VLANs a manual configured Port is member of
                for vlan_nb in [VLAN.get(vlan_id)['number'] for vlan_id in port['retreat_config']['vlans']]:
                    if vlan_nb not in manual_vlans:
                        manual_vlans.append(vlan_nb)

        for vlan_nb in [vlan.id for vlan in swi.vlans]:
            if vlan_nb not in manual_vlans:
                swi.vlanRemove(vlan_nb)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _retreat_vlan_memberships(self):
        """
        Removes all configured VLAN-memberships eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        from elements import VLAN, Port
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            if port['retreat_disabled']:
                continue
            elif port['retreat_config'] is not None:
                # add all VLANs from retreat_config, remove the others
                config_vlans = list()
                for vlan_nb in [VLAN.get(vlan_id)['number'] for vlan_id in port['retreat_config']['vlans']]:
                    config_vlans.append(vlan_nb)
                    swi.vlanAddit(vlan_nb, memberAdd=idx)
                for vlan_nb in [vlan.id for vlan in swi.vlans]:
                    if vlan_nb not in config_vlans:
                        swi.vlanAddit(vlan_nb, memberRemove=idx)
            else:
                # remove all vlans on this port
                for vlan_nb in [vlan.id for vlan in swi.vlans]:
                    swi.vlanAddit(vlan_nb, memberRemove=idx)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _retreat_isolation(self):
        """
        Removes all configured Port-isolations eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            for idy in range(len(swi.ports)):
                if idx == idy:
                    continue
                swi.portEdit(idx, fwdTo=idy)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _retreat_port_vlans(self):
        """
        Removes all Port-level VLAN configuration eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        from elements import VLAN, Port
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            if port['retreat_disabled']:
                # skip disabled ports
                continue
            elif port['retreat_config'] is not None:
                # apply manual port configuration
                vmode = port['retreat_config']['mode']
                if vmode == 'strict' and 'strict' not in swi.vlan_mode_mapping_reverse:
                    vmode = 'enabled'
                vdefault = VLAN.get(port['retreat_config']['default'])['number']
                venabled = port['retreat_config']['enabled']
                vreceive = port['retreat_config']['receive']
                vforce = port['retreat_config']['force']
                swi.portEdit(idx, enabled=venabled, vmode=vmode, vreceive=vreceive, vdefault=vdefault, vforce=vforce)
            else:
                # set default configs
                swi.portEdit(idx, enabled=True, vmode='optional', vreceive='any', vdefault=1, vforce=False)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def retreat(self):
        """
        Removes all configuration eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        from helpers.system import check_integrity_switch_commit
        integrity = check_integrity_switch_commit()
        if not integrity.get('code', 1) == 0:
            return False

        stages = [self._retreat_port_vlans, self._retreat_isolation, self._retreat_vlan_memberships, self._retreat_vlans]
        for stage in stages:
            try:
                if not stage():
                    return False
            except Exception as e:
                print(e)
                print(repr(e))
                return False

        self['commited'] = False
        self.save()
        if self.count() == docDB.count(self.__class__.__name__, {'commited': False}):
            from helpers.system import set_commited
            set_commited(False)

    def _commit_vlans(self):
        """
        Sends VLAN configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import VLAN, Port
        from helpers.switchmgmt import switch_restart_order
        if not self.connected():
            return False

        swi = switch_objects[self['_id']]
        # Add Mgmt VLAN
        for vlan in VLAN.get_by_purpose(1):
            swi.vlanAddit(vlan=vlan['number'])
        # Add Play VLAN
        for vlan in VLAN.get_by_purpose(0):
            swi.vlanAddit(vlan=vlan['number'])
        # determine all onboarding VLANs on this and all subsequent Switches
        for switch_id in switch_restart_order(self['_id']):
            sw = Switch.get(switch_id)
            if sw['onboarding_vlan_id'] is not None:
                onboarding_vlan_nb = VLAN.get(sw['onboarding_vlan_id'])['number']
                swi.vlanAddit(vlan=onboarding_vlan_nb)

        # determine (and add) all VLANs needed by manual port commit configs
        extra_vlans = list()
        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            if not port['commit_disbled'] and port['commit_config'] is not None:
                for vlan_nb in [VLAN.get(vlan_id)['number'] for vlan_id in port['commit_config'].get('vlans', list())]:
                    if vlan_nb not in extra_vlans:
                        extra_vlans.append(vlan_nb)
            if 'other_vlans' in port['commit_config']:
                for vlan_nb in [VLAN.get(vlan_id)['number'] for vlan_id in port['commit_config']['other_vlans']]:
                    if vlan_nb not in extra_vlans:
                        extra_vlans.append(vlan_nb)
        for vlan_nb in extra_vlans:
            swi.vlanAddit(vlan=vlan_nb)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _commit_vlan_memberships(self):
        """
        Sends VLAN-Port-membership configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import VLAN, Device, Port
        from helpers.switchmgmt import switch_restart_order
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        # Get Onboarding VLAN number
        onboarding_vlan_nb = None
        if self['onboarding_vlan_id'] is not None:
            onboarding_vlan_nb = self.onboarding_vlan()['number']
        # Get Mgmt VLAN number
        mgmt_vlan_nb = 1
        for vlan in VLAN.get_by_purpose(1):
            mgmt_vlan_nb = vlan['number']
        # Get Play VLAN number
        play_vlan_nb = 1
        for vlan in VLAN.get_by_purpose(0):
            play_vlan_nb = vlan['number']
        # Cache the LPOS-Port
        lpos_port = Port.get_lpos()

        for idx in range(len(swi.ports)):
            vlans_needed = list()
            port = Port.get_by_number(self['_id'], idx)
            if port == lpos_port:
                # add mgmt- and play-VLAN
                vlans_needed.append(mgmt_vlan_nb)
                vlans_needed.append(play_vlan_nb)
                # add all onboarding-VLANs
                for switch_id in switch_restart_order(self['_id']):
                    sw = Switch.get(switch_id)
                    if sw['onboarding_vlan_id'] is not None:
                        vlans_needed.append(sw.onboarding_vlan()['number'])
            elif port['switchlink']:
                # add mgmt- and play-VLAN
                vlans_needed.append(mgmt_vlan_nb)
                vlans_needed.append(play_vlan_nb)
                # add subsequent onboarding-VLANs
                for switch_id in switch_restart_order(port.switchlink_port().switch()):
                    sw = Switch.get(switch_id)
                    if sw['onboarding_vlan_id'] is not None:
                        vlans_needed.append(sw.onboarding_vlan()['number'])
                # add other-VLANs if present
                if 'other_vlans' in port['commit_config']:
                    for ovlan in port['commit_config']['other_vlans']:
                        ovlan_nb = VLAN.get(ovlan)['number']
                        vlans_needed.append(ovlan_nb)
            elif port['commit_disabled']:
                # skip disabled ports
                continue
            elif port['commit_config'] is not None:
                # apply manual port configuration
                for vlan in [VLAN.get(vlan_id) for vlan_id in port['commit_config'].get('vlans')]:  # add manual configured VLANs
                    vlans_needed.append(vlan['number'])
            elif onboarding_vlan_nb is None:
                # this is an core Switch, all not switchlinks get the play-VLAN
                vlans_needed.append(play_vlan_nb)
            elif not port['participants']:
                # not designated to participants, gets play-VLAN but not onboarding-VLAN
                vlans_needed.append(play_vlan_nb)
            else:
                for device in Device.get_by_port(port['_id']):
                    if device['ip'] is not None:
                        # a valid configured Device is connected to this Port, therefor give it access to play-VLAN
                        vlans_needed.append(play_vlan_nb)
                        break
                else:
                    # no configured Device on this Port, connect it to the onboarding-VLAN
                    vlans_needed.append(onboarding_vlan_nb)

            # Finally remove deprecated VLANs from port and add neeed ones
            for vlan_nb in [vlan.id for vlan in swi.portVLANs(idx)]:
                if vlan_nb not in vlans_needed:
                    swi.vlanEdit(vlan=vlan_nb, memberRemove=idx)
            for vlan_nb in vlans_needed:
                swi.vlanEdit(vlan=vlan_nb, memberAdd=idx)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _commit_isolation(self):
        """
        Sends Port-isolation configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import Device, Port
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        # Cache the LPOS-Port
        lpos_port = Port.get_lpos()

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            onboarding = None
            manual_config = False
            if port == lpos_port or port['switchlink'] or self['onboarding_vlan_id'] is None or not port['participants']:
                onboarding = False
            elif port['commit_disabled'] or port['commit_config'] is not None:
                # skip disabled and manual configured ports or rather enable them
                manual_config = True
            else:
                for device in Device.get_by_port(port['_id']):
                    if device['ip'] is not None:
                        # a valid configured Device is connected to this Port, therefor give it access to the network
                        onboarding = False
                        break
                else:
                    # no configured Device on this Port, only give it access to onboarding
                    onboarding = True

            for idy in range(len(swi.ports)):
                if idx == idy:
                    continue
                porty = Port.get_by_number(self['_id'], idy)
                if not onboarding or manual_config or porty == lpos_port or porty['switchlink']:
                    swi.portEdit(idx, fwdTo=idy)
                else:
                    swi.portEdit(idx, fwdNotTo=idy)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _commit_port_vlans(self):
        """
        Sends Port-level VLAN configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import Device, Port, VLAN
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        # Get Onboarding VLAN number
        onboarding_vlan_nb = None
        if self['onboarding_vlan_id'] is not None:
            onboarding_vlan_nb = self.onboarding_vlan()['number']
        # Get Mgmt VLAN number
        mgmt_vlan_nb = 1
        for vlan in VLAN.get_by_purpose(1):
            mgmt_vlan_nb = vlan['number']
        # Get Play VLAN number
        play_vlan_nb = 1
        for vlan in VLAN.get_by_purpose(0):
            play_vlan_nb = vlan['number']
        # Cache the LPOS-Port
        lpos_port = Port.get_lpos()

        vmode = 'strict'
        if 'strict' not in swi.vlan_mode_mapping_reverse:
            vmode = 'enabled'

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            if port == lpos_port:
                # add mgmt-VLAN as default
                swi.portEdit(idx, vmode=vmode, vreceive='any', vdefault=mgmt_vlan_nb, vforce=False)
            elif port['switchlink']:
                # play-VLAN as default
                swi.portEdit(idx, vmode=vmode, vreceive='only tagged', vdefault=play_vlan_nb, vforce=False)
            elif port['commit_disabled']:
                # skip disabled ports
                continue
            elif port['commit_config'] is not None:
                # apply manual port configuration
                vmode = port['commit_config']['mode']
                if vmode == 'strict' and 'strict' not in swi.vlan_mode_mapping_reverse:
                    vmode = 'enabled'
                vdefault = VLAN.get(port['commit_config']['default'])['number']
                venabled = port['commit_config']['enabled']
                vreceive = port['commit_config']['receive']
                vforce = port['commit_config']['force']
                swi.portEdit(idx, enabled=venabled, vmode=vmode, vreceive=vreceive, vdefault=vdefault, vforce=vforce)
            elif onboarding_vlan_nb is None:
                # this is an core Switch, all not switchlinks get the play-VLAN
                swi.portEdit(idx, vmode=vmode, vreceive='only untagged', vdefault=play_vlan_nb, vforce=False)
            elif not port['participants']:
                # not designated to participants, but gets play-VLAN as default
                swi.portEdit(idx, vmode=vmode, vreceive='only untagged', vdefault=play_vlan_nb, vforce=False)
            else:
                for device in Device.get_by_port(port['_id']):
                    if device['ip'] is not None:
                        # a valid configured Device is connected to this Port, therefor defaults to play-VLAN
                        swi.portEdit(idx, vmode=vmode, vreceive='only untagged', vdefault=play_vlan_nb, vforce=False)
                        break
                else:
                    # no configured Device on this Port, defaults to onboarding-VLAN
                    swi.portEdit(idx, vmode=vmode, vreceive='only untagged', vdefault=onboarding_vlan_nb, vforce=False)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def commit(self):
        """
        Sends all required configuration made in LPOS to a (Hardware)Switch
        """
        from helpers.system import check_integrity_switch_commit
        integrity = check_integrity_switch_commit()
        if not integrity.get('code', 1) == 0:
            return False

        stages = [self._commit_vlans, self._commit_vlan_memberships, self._commit_isolation, self._commit_port_vlans]
        for stage in stages:
            try:
                if not stage():
                    return False
            except Exception:
                return False

        self['commited'] = True
        self.save()
        if self.count() == docDB.count(self.__class__.__name__, {'commited': True}):
            from helpers.system import set_commited
            set_commited(True)

    def json(self):
        result = super().json()
        result['connected'] = self.connected()
        result['mac'] = self.mac_addr()
        result['known_vlans'] = self.known_vlans()
        return result
