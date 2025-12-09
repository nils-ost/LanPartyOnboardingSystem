import logging
import cherrypy
from datetime import datetime
from noapiframe import ElementBase, docDB
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
        onboarding_vlan_id=ElementBase.addAttr(default=None, fk='VLAN'),
        port_numbering_offset=ElementBase.addAttr(type=int, default=0)
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
        if self._attr.get('port_numbering_offset', None) is None:
            self['port_numbering_offset'] = 0

    def save_post(self):
        from elements import Port
        global switch_objects
        test_suite = 'environment' in cherrypy.config and cherrypy.config['environment'] == 'test_suite'
        if not test_suite:
            switch_objects[self['_id']] = MikroTikSwitch(self['addr'], self['user'], self['pw'])
        if self.connected():
            self.scan_vlans()
            self.scan_ports()
        for p in docDB.search_many('Port', {'switch_id': self['_id']}):
            port = Port(p)
            port['number_display'] = port['number'] + self['port_numbering_offset']
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
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]
        swi.reloadPorts()
        swi.reloadHosts()
        return True

    def map_devices(self):
        global switch_objects
        global switch_macs
        from elements import Device, Port
        from helpers.backgroundworker import port_onboarding_schedule
        logger = logging.getLogger('Switch - map_devices')
        if not self.connected():
            return 0
        new_count = 0
        swi = switch_objects[self['_id']]
        for port in swi.ports:
            p = Port.get_by_number(self['_id'], port.idx)
            if p is None:
                continue
            switchlink = False
            for host in port.hosts:
                send_port_update = None
                if host in switch_macs:
                    switchlink = True
                    continue  # this host is a switch, switches are not handled here
                device = Device.get_by_mac(host)
                if device is None and not p['switchlink']:
                    # new Device detected on this Port
                    device = Device({'mac': host, 'port_id': p['_id']})
                    new_count += 1
                    logger.info(f'{repr(device)} first encounter on Port {repr(p)}')
                elif device is None:
                    # skip as this is a switchlink port and regular devices are not connected on switchlink ports
                    pass
                elif p['switchlink'] and device['port_id'] is not None and device['port_id'] == p['_id']:
                    # remove the port from this device as the current port is a switchlink port, those do not connect devices
                    device['port_id'] = None
                    logger.info(f'{repr(device)} removed Port {repr(p)} as this is a switchlink port')
                elif not p['switchlink'] and device['port_id'] is None:
                    # Device was known, but not connected to a Port yet
                    device.port(p)
                    logger.info(f'{repr(device)} assigend to Port {repr(p)}')
                elif not p['switchlink'] and device['port_id'] is not None and not device['port_id'] == p['_id']:
                    # Device was connected to a different Port
                    old_port = device.port()
                    logger.info(f'{repr(device)} switched Port from {repr(old_port)} to {repr(p)}')
                    try:
                        hw_port = switch_objects[old_port['switch_id']].ports[old_port['number']]
                        if host not in hw_port.hosts or len(port.hosts) <= len(hw_port.hosts):
                            send_port_update = old_port['_id']
                            device.port(p)
                    except Exception as e:
                        logger.error(f'{repr(e)}')
                if device is not None:
                    device['last_scan_ts'] = int(datetime.now().timestamp())
                    device.save()  # generic save for everything happend above
                    if send_port_update is not None:
                        # Port of Device changed, reconfigure old an new Port on switch
                        logger.info(f'{repr(device)} switched Port ... sending updates to HWSwitches')
                        port_onboarding_schedule(send_port_update)
                        port_onboarding_schedule(device['port_id'])
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
        swi.reloadPorts()
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
        from elements import VLAN, Port, PortConfigCache
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]
        swi.setMgmtVlan(None)

        # collect vlan_ids needed on this switch
        vlans_needed = list()
        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=1)
            for vlan_id in pcc['vlan_ids']:
                if vlan_id not in vlans_needed:
                    vlans_needed.append(vlan_id)
        # translate vlan_ids to their numbers
        vlans_numbers = [VLAN.get(vlan_id)['number'] for vlan_id in vlans_needed]
        # remove vlans not needed
        for vlan_nb in [vlan.id for vlan in swi.vlans]:
            if vlan_nb not in vlans_numbers:
                swi.vlanRemove(vlan_nb)
        # add needed vlans to switch
        for vlan_nb in sorted(vlans_numbers):
            swi.vlanAddit(vlan_nb)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _retreat_vlan_memberships(self):
        """
        Removes all configured VLAN-memberships eventually made by LPOS from a (Hardware)Switch
        but the Switch-Configuration within LPOS is left untouched
        """
        from elements import VLAN, Port, PortConfigCache
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=1)

            vlans_numbers = [VLAN.get(vlan_id)['number'] for vlan_id in pcc['vlan_ids']]
            for vlan in swi.vlans:
                if idx in vlan._member and vlan.id not in vlans_numbers:
                    swi.vlanEdit(vlan.id, memberRemove=idx)
                if idx not in vlan._member and vlan.id in vlans_numbers:
                    swi.vlanEdit(vlan.id, memberAdd=idx)

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
        from elements import Port, PortConfigCache
        global switch_objects
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=1)
            vmode = pcc['mode']
            if vmode == 'strict' and 'strict' not in swi.vlan_mode_mapping_reverse:
                vmode = 'enabled'
            vdefault = pcc.default_vlan()['number']
            swi.portEdit(idx, enabled=pcc['enabled'], vmode=vmode, vreceive=pcc['receive'], vdefault=vdefault, vforce=pcc['force'])

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
            from elements import Setting
            Setting.set('system_commited', False)

    def _commit_vlans(self):
        """
        Sends VLAN configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import VLAN, Port, PortConfigCache
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        # collect vlan_ids needed on this switch
        vlans_needed = list()
        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=0)
            for vlan_id in pcc['vlan_ids']:
                if vlan_id not in vlans_needed:
                    vlans_needed.append(vlan_id)
        # translate vlan_ids to their numbers
        vlans_numbers = [VLAN.get(vlan_id)['number'] for vlan_id in vlans_needed]
        # remove vlans not needed
        for vlan_nb in [vlan.id for vlan in swi.vlans]:
            if vlan_nb not in vlans_numbers:
                swi.vlanRemove(vlan_nb)
        # add needed vlans to switch
        for vlan_nb in sorted(vlans_numbers):
            swi.vlanAddit(vlan_nb)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _commit_vlan_memberships(self):
        """
        Sends VLAN-Port-membership configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import VLAN, Port, PortConfigCache
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=0)

            vlans_numbers = [VLAN.get(vlan_id)['number'] for vlan_id in pcc['vlan_ids']]
            for vlan in swi.vlans:
                if idx in vlan._member and vlan.id not in vlans_numbers:
                    swi.vlanEdit(vlan.id, memberRemove=idx)
                if idx not in vlan._member and vlan.id in vlans_numbers:
                    swi.vlanEdit(vlan.id, memberAdd=idx)

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def _commit_isolation(self):
        """
        Sends Port-isolation configuration made in LPOS to a (Hardware)Switch
        """
        global switch_objects
        from elements import Port, PortConfigCache
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]
        # cache LPOS Port
        lpos_port = Port.get_lpos()
        lpos_port_nb = lpos_port['number'] if lpos_port['switch_id'] == self['_id'] else -1
        # cache switchlink Ports (numbers) of this Switch
        switchlink_nbs = [p['number'] for p in Port.get_switchlinks(switch_id=self['_id'])]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=0)

            for idy in range(len(swi.ports)):
                if idx == idy:
                    continue
                # isolation of a Port needs to be ignored if the destination is LPOS or a switchlink
                if not pcc['isolate'] or idy == lpos_port_nb or idy in switchlink_nbs:
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
        from elements import Port, PortConfigCache
        if not self.connected():
            return False
        swi = switch_objects[self['_id']]

        for idx in range(len(swi.ports)):
            port = Port.get_by_number(self['_id'], idx)
            pcc = PortConfigCache.get_by_port(port['_id'], scope=0)
            vmode = pcc['mode']
            if vmode == 'strict' and 'strict' not in swi.vlan_mode_mapping_reverse:
                vmode = 'enabled'
            vdefault = pcc.default_vlan()['number']
            swi.portEdit(idx, enabled=pcc['enabled'], vmode=vmode, vreceive=pcc['receive'], vdefault=vdefault, vforce=pcc['force'])

        swi.commitNeeded()
        swi.reloadAll()
        return True

    def commit(self):
        """
        Sends all required configuration made in LPOS to a (Hardware)Switch
        """
        self['commited'] = False
        self.save()

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
            from elements import Setting
            Setting.set('system_commited', True)

    def json(self):
        result = super().json()
        result['connected'] = self.connected()
        result['mac'] = self.mac_addr()
        result['known_vlans'] = self.known_vlans()
        return result
