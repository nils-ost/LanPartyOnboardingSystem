import requests
import logging
from .baseswitch import BaseSwitch
from .parts import SwitchPort, SwitchVLAN


class DummySwitch(BaseSwitch):
    speed_mapping = {
        '10M': '10M',
        '100M': '100M',
        '1G': '1G',
        '10G': '10G',
        'null': None
    }

    vlan_mode_mapping = {
        'disabled': 'disabled',
        'optional': 'optional',
        'enabled': 'enabled',
        'strict': 'strict'
    }

    vlan_receive_mapping = {
        'any': 'any',
        'only tagged': 'only tagged',
        'only untagged': 'only untagged'
    }

    def __init__(self, host, user, password):
        super().__init__(host, user, password)
        self.logger = logging.getLogger('DummySwitch')
        self.vendor = 'nils_ost'
        self.model = 'dummy'
        self._conn = requests.session()
        self.loadAll()

    def _getData(self, doc):
        try:
            url = f'http://{self._host}/{doc}/'
            self.logger.debug(f'getData:{url}')
            r = self._conn.get(url, timeout=0.1)
            self.logger.debug(f'getData:{r.text}')
            self.connected = True
            return r.json()
        except Exception as e:
            self.logger.debug(f'getData:exception:{repr(e)}')
            self.connected = False
            return dict()

    def _postData(self, doc, data):
        try:
            url = f'http://{self._host}/{doc}/'
            self.logger.info(f'postData:{url}')
            self.logger.debug(f'postData:{data}')
            r = self._conn.post(url, json=data, timeout=0.2)
            self.logger.debug(f'postData:status_code:{r.status_code}')
            self.connected = True
        except Exception as e:
            self.logger.debug(f'postData:exception:{repr(e)}')
            self.connected = False

    def loadSystem(self, response=None):
        """
        reads: identity, mac_addr, mgmt_vlan
        """
        if response is None:
            r = self._getData('system')
            if len(r) == 0:
                self.logger.error(f"loadSystem ({self._host}): Couldn't fetch data")
                return
        else:
            r = response
        self.identity = r.get('identity', '')
        self.mac_addr = r.get('mac_addr', '')
        self.mgmt_vlan = int(r.get('mgmt_vlan', 0))
        if self.mgmt_vlan == 0:
            self.mgmt_vlan = None
        self._commitUnregister('system')

    def loadPorts(self, response=None):
        """
        reads: gbe-count, sfp-count, total-count
        """
        if response is None:
            self.ports = list()
            r = self._getData('ports')
            for t in ['gbe'] * int(r.get('gbe-count', 0)) + ['sfp+'] * int(r.get('sfp-count', 0)):
                p = SwitchPort()
                p.type = t
                self.ports.append(p)
        else:
            r = response

        if not len(self.ports) == int(r.get('total-count', 0)):
            self.logger.error(f"loadPorts ({self._host}): Detected port-count doesn't match reported port-count")
        self.reloadPorts(r)
        self._commitUnregister('ports')

    def reloadPorts(self, response=None):
        """
        reads: config(idx, en, link, name, spd)
        """
        if response is None:
            r = self._getData('ports')
        else:
            r = response
        for p in r.get('config', list()):
            idx = int(p.get('idx', 0))
            self.ports[idx].idx = idx
            self.ports[idx].enabled = bool(p.get('en', False))
            self.ports[idx].link = bool(p.get('link', False))
            self.ports[idx].name = p.get('name', '')
            spd = p.get('spd', 'unknown')
            if spd not in self.speed_mapping:
                self.logger.warning(f"loadPorts ({self._host}): Detected speed {spd} can't be found in speed_mapping, replacing it by None")
                spd = None
            else:
                spd = self.speed_mapping[spd]
            self.ports[idx].speed = spd
        self._commitUnregister('ports')

    def loadIsolation(self, response=None):
        """
        reads: from*
        """
        if response is None:
            r = self._getData('isolation')
        else:
            r = response
        port_count = len(self.ports)
        for port in self.ports:
            fwd = r.get(f'from{port.idx}', '0b0').replace('0b', '')
            fwd = fwd[::-1] + '0' * (port_count - len(fwd))
            for idx in range(port_count):
                if fwd[idx] == '1':
                    port.fwdTo(idx)
                else:
                    port.fwdNotTo(idx)
        self._commitUnregister('isolation')

    def loadHosts(self, response=None):
        """
        reads: *(port, addr)
        """
        if response is None:
            r = self._getData('hosts')
        else:
            r = response
        hosts = dict()
        for host in r:
            port = int(host.get('port', 0))
            if port not in hosts:
                hosts[port] = list()
            hosts[port].append(host.get('addr', ''))
        for idx in range(len(self.ports)):
            if idx in hosts:
                self.ports[idx].hosts = hosts[idx]
            else:
                self.ports[idx].hosts = list()

    def loadVlans(self, response=None):
        """
        reads: *(id, isolation, learning, mirror, igmp, member)
        """
        if response is None:
            r = self._getData('vlans')
        else:
            r = response
        self.vlans = list()
        for vlan in r:
            vlan_obj = SwitchVLAN()
            vlan_obj.id = int(vlan.get('id', 0))
            vlan_obj.isolation = bool(vlan.get('piso', True))
            vlan_obj.learning = bool(vlan.get('learning', True))
            vlan_obj.mirror = bool(vlan.get('mirror', False))
            vlan_obj.igmp = bool(vlan.get('igmp', False))
            mbr = vlan.get('member', '0b0').replace('0b', '')
            mbr = mbr[::-1] + '0' * (len(self.ports) - len(mbr))
            for idx in range(len(mbr)):
                if mbr[idx] == '1':
                    vlan_obj.memberAdd(idx)
            self.vlans.append(vlan_obj)
        self._commitUnregister('vlans')

    def loadPortsVlan(self, response=None):
        """
        reads: idx*(mode, receive, default, force)
        """
        if response is None:
            r = self._getData('ports_vlans')
        else:
            r = response
        for idx in range(len(self.ports)):
            if f'idx{idx}' not in r:
                continue
            port = r.get(f'idx{idx}')
            mode = port.get('mode', 'unknown')
            if mode not in self.vlan_mode_mapping:
                self.logger.warning(f"loadPortsVlan ({self._host}): Detected vlan_mode {mode} can't be found in vlan_mode_mapping")
            else:
                self.ports[idx].vlan_mode = self.vlan_mode_mapping[mode]
            receive = port.get('receive', 'unknown')
            if receive not in self.vlan_receive_mapping:
                self.logger.warning(f"loadPortsVlan ({self._host}): Detected vlan_receive {receive} can't be found in vlan_receive_mapping")
            else:
                self.ports[idx].vlan_receive = self.vlan_receive_mapping[receive]
            self.ports[idx].vlan_default = int(port.get('default', '1'))
            self.ports[idx].vlan_force = bool(port.get('force', False))
        self._commitUnregister('portsvlan')

    def commitSystem(self, request=None):
        if self.mgmt_vlan is None:
            mgmtvlan = 0
        else:
            mgmtvlan = self.mgmt_vlan
        self._postData('system', {'mgmt_vlan': mgmtvlan})
        self._commitUnregister('system')

    def commitPorts(self, request=None):
        r = list()
        for port in self.ports:
            r.append(dict(
                idx=port.idx,
                en=port.enabled,
                name=port.name
            ))
        self._postData('ports', r)
        self._commitUnregister('ports')

    def commitIsolation(self, request=None):
        r = dict()
        for port in self.ports:
            fwd = ''
            for idx in range(len(self.ports)):
                fwd += '1' if idx in port._fwd else '0'
            fwd = '0b' + fwd
            r[f'from{port.idx}'] = fwd
        self._postData('isolation', r)
        self._commitUnregister('isolation')

    def commitVlans(self, request=None):
        r = list()
        for vlan in self.vlans:
            {'id': 1, 'isolation': True, 'learning': True, 'mirror': False, 'igmp': False, 'member': '0b1111111111'}
            mbr = ''
            for idx in range(len(self.ports)):
                mbr += '1' if idx in vlan._member else '0'
            mbr = '0b' + mbr
            r.append(dict(
                id=vlan.id,
                isolation=vlan.isolation,
                learning=vlan.learning,
                mirror=vlan.mirror,
                igmp=vlan.igmp,
                member=mbr
            ))
        self._postData('vlans', r)
        self._commitUnregister('vlans')

    def commitPortsVlan(self, request=None):
        r = dict()
        for port in self.ports:
            p = dict()
            if port.vlan_mode not in self.vlan_mode_mapping_reverse:
                self.logger.error(
                    f'commitPortsVlan ({self._host}): vlan_mode {port.vlan_mode} of Port {port.idx} not found in vlan_mode_mapping_reverse. Assuming optional')
                p['mode'] = 'optional'
            else:
                p['mode'] = self.vlan_mode_mapping_reverse[port.vlan_mode]
            if port.vlan_receive not in self.vlan_receive_mapping_reverse:
                msg = ' '.join([
                    f'commitPortsVlan ({self._host}): vlan_receive {port.vlan_receive} of Port {port.idx}',
                    'not found in vlan_receive_mapping_reverse. Assuming only untagged'])
                self.logger.error(msg)
                p['receive'] = 'only untagged'
            else:
                p['receive'] = self.vlan_receive_mapping_reverse[port.vlan_receive]
            p['default'] = str(port.vlan_default)
            p['force'] = port.vlan_force
            r[f'idx{port.idx}'] = p
        self._postData('ports_vlans', r)
        self._commitUnregister('portsvlan')
