import logging
import json
from .parts import SwitchPort, SwitchVLAN


class BaseSwitch(object):
    speed_mapping = {
        'value_indicating_10M': '10M',
        'value_indicating_100M': '100M',
        'value_indicating_1G': '1G',
        'value_indicating_10G': '10G',
        'value_indicating_none': None
    }
    # ensure vlan_mode_mapping_reverse does have the keys: [disabled, optional, enabled, strict] if you choose to alter this mapping
    vlan_mode_mapping = {
        'value_indicating_disabled': 'disabled',
        'value_indicating_optional': 'optional',
        'value_indicating_enabled': 'enabled',
        'value_indicating_strict': 'strict'
    }
    # ensure vlan_receive_mapping_reverse does have the keys: [any, only tagged, only untagged] if you choose to alter this mapping
    vlan_receive_mapping = {
        'value_indicating_any': 'any',
        'value_indicating_tagged': 'only tagged',
        'value_indicating_untagged': 'only untagged'
    }

    def __init__(self, host, user, password):
        self.vendor = 'none'
        self.model = 'base'
        self.identity = ''
        self.mac_addr = ''
        self.mgmt_vlan = None
        self.ports = list()
        self.vlans = list()
        self._host = host
        self._conn = None
        self._pending_commits = list()
        self.connected = False
        self.vlan_mode_mapping_reverse = dict([(v, k) for k, v in self.vlan_mode_mapping.items()])
        self.vlan_receive_mapping_reverse = dict([(v, k) for k, v in self.vlan_receive_mapping.items()])
        self.logger = logging.getLogger('BaseSwitch')

    def __str__(self):
        return json.dumps(self.json())

    def _commitRegister(self, component):
        if component not in self._pending_commits:
            self._pending_commits.append(component)

    def _commitUnregister(self, component):
        if component in self._pending_commits:
            self._pending_commits.remove(component)

    def loadAll(self):
        self.loadSystem()
        self.loadPorts()
        self.loadIsolation()
        self.loadHosts()
        self.loadVlans()
        self.loadPortsVlan()

    def loadSystem(self, response=None):
        raise NotImplementedError

    def loadPorts(self, response=None):
        raise NotImplementedError

    def loadIsolation(self, response=None):
        raise NotImplementedError

    def loadHosts(self, response=None):
        raise NotImplementedError

    def loadVlans(self, response=None):
        raise NotImplementedError

    def loadPortsVlan(self, response=None):
        raise NotImplementedError

    def reloadAll(self):
        self.reloadSystem()
        self.reloadPorts()
        self.reloadIsolation()
        self.reloadHosts()
        self.reloadVlans()
        self.reloadPortsVlan()

    def reloadSystem(self, response=None):
        self.loadSystem(response)
        self._commitUnregister('system')

    def reloadPorts(self, response=None):
        self.loadPorts(response)
        self._commitUnregister('ports')

    def reloadIsolation(self, response=None):
        self.loadIsolation(response)
        self._commitUnregister('isolation')

    def reloadHosts(self, response=None):
        self.loadHosts(response)

    def reloadVlans(self, response=None):
        self.loadVlans(response)
        self._commitUnregister('vlans')

    def reloadPortsVlan(self, response=None):
        self.loadPortsVlan(response)
        self._commitUnregister('portsvlan')

    def commitAll(self):
        self.commitPorts()
        self.commitVlans()
        self.commitIsolation()
        self.commitPortsVlan()
        self.commitSystem()

    def commitSystem(self, request=None):
        raise NotImplementedError

    def commitPorts(self, request=None):
        raise NotImplementedError

    def commitIsolation(self, request=None):
        raise NotImplementedError

    def commitVlans(self, request=None):
        raise NotImplementedError

    def commitPortsVlan(self, request=None):
        raise NotImplementedError

    def commitNeeded(self):
        while len(self._pending_commits) > 0:
            pending = self._pending_commits[0]
            if pending == 'ports':
                self.commitPorts()
            elif pending == 'vlans':
                self.commitVlans()
            elif pending == 'isolation':
                self.commitIsolation()
            elif pending == 'portsvlan':
                self.commitPortsVlan()
            elif pending == 'system':
                self.commitSystem()

    def portEdit(self, port, enabled=None, fwdTo=None, fwdNotTo=None, vmode=None, vreceive=None, vdefault=None, vforce=None):
        if isinstance(port, SwitchPort):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error(f'portEdit ({self._host}): port needs to be an instance of int or SwitchPort')
            return
        if port not in range(len(self.ports)):
            self.logger.error(f'portEdit ({self._host}): index {port} not in range of available ports')
            return
        if enabled is not None:
            if isinstance(enabled, bool):
                if not enabled == self.ports[port].enabled:
                    self.ports[port].enabled = enabled
                    self._commitRegister('ports')
            else:
                self.logger.error(f'portEdit ({self._host}): enabled needs to be instance of bool')
        if fwdTo is not None:
            if self.ports[port].fwdTo(fwdTo):
                self._commitRegister('isolation')
        if fwdNotTo is not None:
            if self.ports[port].fwdNotTo(fwdNotTo):
                self._commitRegister('isolation')
        if vmode is not None:
            if vmode in self.vlan_mode_mapping:
                vmode = self.vlan_mode_mapping[vmode]
            if vmode in self.vlan_mode_mapping_reverse:
                if not vmode == self.ports[port].vlan_mode:
                    self.ports[port].vlan_mode = vmode
                    self._commitRegister('portsvlan')
            else:
                self.logger.error(f'portEdit ({self._host}): unknown vmode {vmode}')
        if vreceive is not None:
            if vreceive in self.vlan_receive_mapping:
                vreceive = self.vlan_receive_mapping[vreceive]
            if vreceive in self.vlan_receive_mapping_reverse:
                if not vreceive == self.ports[port].vlan_receive:
                    self.ports[port].vlan_receive = vreceive
                    self._commitRegister('portsvlan')
            else:
                self.logger.error(f'portEdit ({self._host}): unknown vreceive {vreceive}')
        if vdefault is not None:
            if vdefault == 1:
                if not self.ports[port].vlan_default == 1:
                    self.ports[port].vlan_default = 1
                    self._commitRegister('portsvlan')
            else:
                for vlan in self.vlans:
                    if vlan.id == vdefault:
                        if not self.ports[port].vlan_default == vdefault:
                            self.ports[port].vlan_default = vdefault
                            self._commitRegister('portsvlan')
                        break
                else:
                    self.logger.error(f'portEdit ({self._host}): unknown vdefault {vdefault}')
        if vforce is not None:
            if isinstance(vforce, bool):
                if not vforce == self.ports[port].vlan_force:
                    self.ports[port].vlan_force = vforce
                    self._commitRegister('portsvlan')
            else:
                self.logger.error(f'portEdit ({self._host}): vforce needs to instance of bool')

    def portVLANs(self, port):
        if isinstance(port, SwitchPort):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error(f'portVLANs ({self._host}): port needs to be an instance of int or SwitchPort')
            return
        if port not in range(len(self.ports)):
            self.logger.error(f'portVLANs ({self._host}): index {port} not in range of available ports')
            return

        result = list()
        for vlan in self.vlans:
            if port in vlan._member:
                result.append(vlan)
        return result

    def vlanEdit(self, vlan, isolation=None, learning=None, mirror=None, igmp=None, memberAdd=None, memberRemove=None):
        if isinstance(vlan, SwitchVLAN):
            vlan = vlan.id
        elif not isinstance(vlan, int):
            self.logger.error(f'vlanEdit ({self._host}): vlan needs to be an instance of int or SwitchVLAN')
            return
        for idx in range(len(self.vlans)):
            if vlan == self.vlans[idx].id:
                break
        else:
            self.logger.error(f'vlanEdit ({self._host}): unknown vlan {vlan}')
            return
        if isolation is not None:
            if isinstance(isolation, bool):
                if not isolation == self.vlans[idx].isolation:
                    self.vlans[idx].isolation = isolation
                    self._commitRegister('vlans')
            else:
                self.logger.error(f'vlanEdit ({self._host}): isolation needs to be an instance bool')
        if learning is not None:
            if isinstance(learning, bool):
                if not learning == self.vlans[idx].learning:
                    self.vlans[idx].learning = learning
                    self._commitRegister('vlans')
            else:
                self.logger.error(f'vlanEdit ({self._host}): learning needs to be an instance bool')
        if mirror is not None:
            if isinstance(mirror, bool):
                if not mirror == self.vlans[idx].mirror:
                    self.vlans[idx].mirror = mirror
                    self._commitRegister('vlans')
            else:
                self.logger.error(f'vlanEdit ({self._host}): mirror needs to be an instance bool')
        if igmp is not None:
            if isinstance(igmp, bool):
                if not igmp == self.vlans[idx].igmp:
                    self.vlans[idx].igmp = igmp
                    self._commitRegister('vlans')
            else:
                self.logger.error(f'vlanEdit ({self._host}): igmp needs to be an instance bool')
        if memberAdd is not None:
            if self.vlans[idx].memberAdd(memberAdd):
                self._commitRegister('vlans')
        if memberRemove is not None:
            if self.vlans[idx].memberRemove(memberRemove):
                self._commitRegister('vlans')

    def vlanAdd(self, vlan, isolation=None, learning=None, mirror=None, igmp=None, memberAdd=None, memberRemove=None):
        if isinstance(vlan, SwitchVLAN):
            for v in self.vlans:
                if v.id == vlan.id:
                    self.logger.error(f'vlanAdd ({self._host}): vlan with id {vlan.id} allready present')
                    break
            else:
                self.vlans.append(vlan)
                self._commitRegister('vlans')
        elif isinstance(vlan, int):
            for v in self.vlans:
                if v.id == vlan:
                    self.logger.error(f'vlanAdd ({self._host}): vlan with id {vlan} allready present')
                    break
            else:
                v = SwitchVLAN()
                v.id = vlan
                self.vlans.append(v)
                self._commitRegister('vlans')
                self.vlanEdit(vlan, isolation=isolation, learning=learning, mirror=mirror, igmp=igmp, memberAdd=memberAdd, memberRemove=memberRemove)
        else:
            self.logger.error(f'vlanAdd ({self._host}): vlan needs to be an instance of int or SwitchVLAN')

    def vlanAddit(self, vlan, isolation=None, learning=None, mirror=None, igmp=None, memberAdd=None, memberRemove=None):
        """
        Add or Edit a VLAN
        """
        if isinstance(vlan, SwitchVLAN):
            vlan = vlan.id
        elif not isinstance(vlan, int):
            self.logger.error(f'vlanAddit ({self._host}): vlan needs to be an instance of int or SwitchVLAN')
            return
        for idx in range(len(self.vlans)):
            if vlan == self.vlans[idx].id:
                self.vlanEdit(vlan=vlan, isolation=isolation, learning=learning, mirror=mirror, igmp=igmp, memberAdd=memberAdd, memberRemove=memberRemove)
                break
        else:
            self.vlanAdd(vlan=vlan, isolation=isolation, learning=learning, mirror=mirror, igmp=igmp, memberAdd=memberAdd, memberRemove=memberRemove)

    def vlanRemove(self, vlan):
        if isinstance(vlan, SwitchVLAN):
            vlan = vlan.id
        elif not isinstance(vlan, int):
            self.logger.error(f'vlanRemove ({self._host}): vlan needs to be an instance of int or SwitchVLAN')
            return
        for idx in range(len(self.vlans)):
            if self.vlans[idx].id == vlan:
                self.vlans.pop(idx)
                self._commitRegister('vlans')
                break
        else:
            self.logger.warning(f'vlanRemove: vlan with id {vlan} was not present')

    def setMgmtVlan(self, vlan=None):
        if vlan is None:
            self.mgmt_vlan = None
            self._commitRegister('system')
            return
        elif isinstance(vlan, SwitchVLAN):
            vlan = vlan.id
        elif not isinstance(vlan, int):
            self.logger.error(f'setMgmtVlan ({self._host}): vlan needs to be an instance of int, SwitchVLAN or None')
            return
        for idx in range(len(self.vlans)):
            if self.vlans[idx].id == vlan:
                self.mgmt_vlan = vlan
                self._commitRegister('system')
                break
        else:
            self.logger.error(f'setMgmtVlan ({self._host}): vlan with id {vlan} is not present')

    def json(self):
        r = dict(
            vendor=self.vendor,
            model=self.model,
            identity=self.identity,
            mac_addr=self.mac_addr,
            mgmt_vlan=self.mgmt_vlan
        )
        r['vlans'] = list()
        for v in self.vlans:
            r['vlans'].append(v.json())
        r['ports'] = list()
        for p in self.ports:
            r['ports'].append(p.json())
        return r
