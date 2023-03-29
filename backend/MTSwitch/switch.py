import requests
from requests.auth import HTTPDigestAuth
import logging
from .helpers import responseToJson, asciiToStr, jsonToRequest, strToAscii
from .parts import SwitchPort, SwitchVLAN


model_mapping = dict()
speed_mapping = {
    '0x01': '100M',
    '0x02': '1G',
    '0x07': None
}
vlan_mode_mapping = {
    '0x00': 'disabled',
    '0x01': 'optional',
    '0x02': 'enabled',
    '0x03': 'strict'
}
vlan_mode_mapping_reverse = dict([(v, k) for k, v in vlan_mode_mapping.items()])
vlan_receive_mapping = {
    '0x00': 'any',
    '0x01': 'only tagged',
    '0x02': 'only untagged'
}
vlan_receive_mapping_reverse = dict([(v, k) for k, v in vlan_receive_mapping.items()])


class MikroTikSwitch():
    logger = logging.getLogger('MikroTikSwitch')

    def __init__(self, host, user, password):
        self.model = 'generic'
        self.identity = ''
        self.mac_addr = ''
        self.ports = list()
        self.vlans = list()
        self._host = host
        self._conn = requests.session()
        self._conn.auth = HTTPDigestAuth(user, password)
        self._pending_commits = list()
        self.connected = False
        self.loadSystem()

    def _commitRegister(self, component):
        if component not in self._pending_commits:
            self._pending_commits.append(component)

    def _commitUnregister(self, component):
        if component in self._pending_commits:
            self._pending_commits.remove(component)

    def getData(self, doc, toJson=True):
        self.connected = True
        try:
            url = f'http://{self._host}/{doc}'
            self.logger.info(f'getData:{url}')
            r = self._conn.get(url)
            self.logger.debug(f'getData:{r.text}')
            if toJson:
                return responseToJson(r.text)
            return r.text
        except Exception as e:
            self.logger.debug(f'getData:exception:{repr(e)}')
            self.connected = False
            if toJson:
                return dict()
            return ''

    def postData(self, doc, data):
        self.connected = True
        try:
            url = f'http://{self._host}/{doc}'
            data = jsonToRequest(data)
            self.logger.info(f'postData:{url}')
            self.logger.debug(f'postData:{data}')
            r = self._conn.post(url, data=data)
            self.logger.debug(f'postData:status_code:{r.status_code}')
        except Exception as e:
            self.logger.debug(f'postData:exception:{repr(e)}')
            self.connected = False

    def loadSystem(self):
        r = self.getData('sys.b')
        self.identity = asciiToStr(r.get('id', ''))
        self.mac_addr = r.get('mac', '')
        model = asciiToStr(r.get('brd', ''))
        if not model == self.model and model in model_mapping:
            self.model = model
            self.__class__ = model_mapping[model]
        self.loadPorts()
        self.loadIsolation()
        self.loadHosts()
        self.loadVlans()
        self.loadPortsVlan()

    def loadPorts(self, response=None):
        if response is None:
            self.ports = list()
            r = self.getData('link.b')
            for t in ['gbe'] * int(r.get('sfpo', '0'), 16):
                p = SwitchPort()
                p.type = t
                self.ports.append(p)
        else:
            r = response

        if not len(self.ports) == int(r.get('prt', '0'), 16):
            self.logger.error("loadPorts: Detected port-count doesn't match reported port-count")
        self.reloadPorts(r)
        self._commitUnregister('ports')

    def reloadPorts(self, response=None):
        if response is None:
            r = self.getData('link.b')
        else:
            r = response
        port_count = len(self.ports)
        lnk = bin(int(r.get('lnk', '0'), 16))
        lnk = lnk[::-1] + '0' * (port_count - len(lnk))
        en = bin(int(r.get('en', '0'), 16))
        en = en[::-1] + '0' * (port_count - len(en))
        for idx in range(port_count):
            self.ports[idx].idx = idx
            self.ports[idx].enabled = en[idx] == '1'
            self.ports[idx].link = lnk[idx] == '1'
            self.ports[idx].name = asciiToStr(r.get('nm', list())[idx])
            spd = r.get('spd', list())[idx]
            if spd not in speed_mapping:
                self.logger.warning(f"loadPorts: Detected speed {spd} can't be found in speed_mapping, replacing it by None")
                spd = None
            else:
                spd = speed_mapping[spd]
            self.ports[idx].speed = spd
        self._commitUnregister('ports')

    def loadIsolation(self, response=None):
        if response is None:
            r = self.getData('fwd.b')
        else:
            r = response
        port_count = len(self.ports)
        for port in self.ports:
            fwd = r.get(f'fp{port.idx + 1}', '0')
            fwd = bin(int(fwd, 16)).replace('0b', '')
            fwd = fwd[::-1] + '0' * (port_count - len(fwd))
            for idx in range(port_count):
                if fwd[idx] == '1':
                    port.fwdTo(idx)
                else:
                    port.fwdNotTo(idx)
        self._commitUnregister('isolation')

    def reloadIsolation(self, response=None):
        self.loadIsolation(response)
        self._commitUnregister('isolation')

    def loadHosts(self, response=None):
        if response is None:
            r = self.getData('!dhost.b')
        else:
            r = response
        hosts = dict()
        for host in r:
            port = int(host.get('prt', '0'), 16)
            if port not in hosts:
                hosts[port] = list()
            hosts[port].append(host.get('adr', ''))
        for idx in range(len(self.ports)):
            if idx in hosts:
                self.ports[idx].hosts = hosts[idx]
            else:
                self.ports[idx].hosts = list()

    def reloadHosts(self, response=None):
        self.loadHosts(response)

    def loadVlans(self, response=None):
        if response is None:
            r = self.getData('vlan.b')
        else:
            r = response
        self.vlans = list()
        for vlan in r:
            vlan_obj = SwitchVLAN()
            vlan_obj.id = int(vlan.get('vid', '0'), 16)
            vlan_obj.isolation = int(vlan.get('piso', '0'), 16) == 1
            vlan_obj.learning = int(vlan.get('lrn', '0'), 16) == 1
            vlan_obj.mirror = int(vlan.get('mrr', '0'), 16) == 1
            vlan_obj.igmp = int(vlan.get('igmp', '0'), 16) == 1
            mbr = bin(int(vlan.get('mbr', '0'), 16)).replace('0b', '')
            mbr = mbr[::-1] + '0' * (len(self.ports) - len(mbr))
            for idx in range(len(mbr)):
                if mbr[idx] == '1':
                    vlan_obj.memberAdd(idx)
            self.vlans.append(vlan_obj)
        self._commitUnregister('vlans')

    def reloadVlans(self, response=None):
        self.loadVlans(response)
        self._commitUnregister('vlans')

    def loadPortsVlan(self, response=None):
        if response is None:
            r = self.getData('fwd.b')
        else:
            r = response
        fvid = bin(int(r.get('fvid', '0'), 16)).replace('0b', '')
        fvid = fvid[::-1] + '0' * (len(self.ports) - len(fvid))
        for idx in range(len(self.ports)):
            mode = r.get('vlan', list())[idx]
            if mode not in vlan_mode_mapping:
                self.logger.warning(f"loadPortsVlan: Detected vlan_mode {mode} can't be found in vlan_mode_mapping")
            else:
                self.ports[idx].vlan_mode = vlan_mode_mapping[mode]
            receive = r.get('vlni', list())[idx]
            if receive not in vlan_receive_mapping:
                self.logger.warning(f"loadPortsVlan: Detected vlan_receive {receive} can't be found in vlan_receive_mapping")
            else:
                self.ports[idx].vlan_receive = vlan_receive_mapping[receive]
            self.ports[idx].vlan_default = int(r.get('dvid', list())[idx], 16)
            self.ports[idx].vlan_force = fvid[idx] == '1'
        self._commitUnregister('portsvlan')

    def reloadPortsVlan(self, response=None):
        self.loadPortsVlan(response)
        self._commitUnregister('portsvlan')

    def commitPorts(self, request=None):
        r = request if request else dict()
        r['nm'] = list()
        en = ''
        for port in self.ports:
            r['nm'].append(f"'{strToAscii(port.name)}'")
            en += '1' if port.enabled else '0'
        en = '0b' + en[::-1]
        en = hex(int(en, 2)).replace('0x', '')
        en = '0x' + '0' * (len(en) % 2) + en
        r['en'] = en
        self.postData('link.b', r)
        self._commitUnregister('ports')

    def commitIsolation(self, request=None):
        r = request if request else dict()
        for port in self.ports:
            fwd = ''
            for idx in range(len(self.ports)):
                fwd += '1' if idx in port._fwd else '0'
            fwd = hex(int(fwd[::-1], 2)).replace('0x', '')
            fwd = '0x' + '0' * (len(fwd) % 2) + fwd
            r[f'fp{port.idx + 1}'] = fwd
        self.postData('fwd.b', r)
        self._commitUnregister('isolation')

    def commitVlans(self, request=None):
        r = request if request else list()
        for vlan in self.vlans:
            v = dict()
            v['vid'] = hex(vlan.id).replace('0x', '')
            v['vid'] = '0x' + '0' * (len(v['vid']) % 2) + v['vid']
            v['piso'] = '0x01' if vlan.isolation else '0x00'
            v['lrn'] = '0x01' if vlan.learning else '0x00'
            v['mrr'] = '0x01' if vlan.mirror else '0x00'
            v['igmp'] = '0x01' if vlan.igmp else '0x00'
            mbr = ''
            for idx in range(len(self.ports)):
                mbr += '1' if idx in vlan._member else '0'
            mbr = hex(int(mbr[::-1], 2)).replace('0x', '')
            v['mbr'] = '0x' + '0' * (len(mbr) % 2) + mbr
            r.append(v)
        self.postData('vlan.b', r)
        self._commitUnregister('vlans')

    def commitPortsVlan(self, request=None):
        r = request if request else dict()
        r['vlan'] = list()
        r['vlni'] = list()
        r['dvid'] = list()
        fvid = ''
        for port in self.ports:
            if port.vlan_mode not in vlan_mode_mapping_reverse:
                self.logger.error(f'commitPortsVlan: vlan_mode {port.vlan_mode} of Port {port.idx} not found in vlan_mode_mapping_reverse. Assumeing 0x02')
                r['vlan'].append('0x02')
            else:
                r['vlan'].append(vlan_mode_mapping_reverse[port.vlan_mode])
            if port.vlan_receive not in vlan_receive_mapping_reverse:
                self.logger.error(
                    f'commitPortsVlan: vlan_receive {port.vlan_receive} of Port {port.idx} not found in vlan_receive_mapping_reverse. Assumeing 0x02')
                r['vlni'].append('0x02')
            else:
                r['vlni'].append(vlan_receive_mapping_reverse[port.vlan_receive])
            dvid = hex(port.vlan_default).replace('0x', '')
            r['dvid'].append('0x' + '0' * (len(dvid) % 2) + dvid)
            fvid += '1' if port.vlan_force else '0'
        fvid = hex(int(fvid[::-1], 2)).replace('0x', '')
        r['fvid'] = '0x' + '0' * (len(fvid) % 2) + fvid
        self.postData('fwd.b', r)
        self._commitUnregister('portsvlan')

    def commitAll(self):
        self.commitPorts()
        self.commitVlans()
        self.commitIsolation()
        self.commitPortsVlan()

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

    def portEdit(self, port, enabled=None, fwdTo=None, fwdNotTo=None, vmode=None, vreceive=None, vdefault=None, vforce=None):
        if isinstance(port, SwitchPort):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error('portEdit: port needs to be an instance of int or SwitchPort')
            return
        if port not in range(len(self.ports)):
            self.logger.error(f'portEdit: index {port} not in range of available ports')
            return
        if enabled is not None:
            if isinstance(enabled, bool):
                if not enabled == self.ports[port].enabled:
                    self.ports[port].enabled = enabled
                    self._commitRegister('ports')
            else:
                self.logger.error('portEdit: enabled needs to be instance of bool')
        if fwdTo is not None:
            if self.ports[port].fwdTo(fwdTo):
                self._commitRegister('isolation')
        if fwdNotTo is not None:
            if self.ports[port].fwdNotTo(fwdNotTo):
                self._commitRegister('isolation')
        if vmode is not None:
            if vmode in vlan_mode_mapping:
                vmode = vlan_mode_mapping[vmode]
            if vmode in vlan_mode_mapping_reverse:
                if not vmode == self.ports[port].vlan_mode:
                    self.ports[port].vlan_mode = vmode
                    self._commitRegister('portsvlan')
            else:
                self.logger.error(f'portEdit: unknown vmode {vmode}')
        if vreceive is not None:
            if vreceive in vlan_receive_mapping:
                vreceive = vlan_receive_mapping[vreceive]
            if vreceive in vlan_receive_mapping_reverse:
                if not vreceive == self.ports[port].vlan_receive:
                    self.ports[port].vlan_receive = vreceive
                    self._commitRegister('portsvlan')
            else:
                self.logger.error(f'portEdit: unknown vreceive {vreceive}')
        if vdefault is not None:
            for vlan in self.vlans:
                if vlan.id == vdefault:
                    if not self.ports[port].vlan_default == vdefault:
                        self.ports[port].vlan_default = vdefault
                        self._commitRegister('portsvlan')
                    break
            else:
                self.logger.error(f'portEdit: unknown vdefault {vdefault}')
        if vforce is not None:
            if isinstance(vforce, bool):
                if not vforce == self.ports[port].vlan_force:
                    self.ports[port].vlan_force = vforce
                    self._commitRegister('portsvlan')
            else:
                self.logger.error('portEdit: vforce needs to instance of bool')

    def vlanEdit(self, vlan, isolation=None, learning=None, mirror=None, igmp=None, memberAdd=None, memberRemove=None):
        if isinstance(vlan, SwitchVLAN):
            vlan = vlan.id
        elif not isinstance(vlan, int):
            self.logger.error('vlanEdit: vlan needs to be an instance of int or SwitchVLAN')
            return
        for idx in range(len(self.vlans)):
            if vlan == self.vlans[idx].id:
                break
        else:
            self.logger.error(f'vlanEdit: unknown vlan {vlan}')
            return
        if isolation is not None:
            if isinstance(isolation, bool):
                if not isolation == self.vlans[idx].isolation:
                    self.vlans[idx].isolation = isolation
                    self._commitRegister('vlans')
            else:
                self.logger.error('vlanEdit: isolation needs to be an instance bool')
        if learning is not None:
            if isinstance(learning, bool):
                if not learning == self.vlans[idx].learning:
                    self.vlans[idx].learning = learning
                    self._commitRegister('vlans')
            else:
                self.logger.error('vlanEdit: learning needs to be an instance bool')
        if mirror is not None:
            if isinstance(mirror, bool):
                if not mirror == self.vlans[idx].mirror:
                    self.vlans[idx].mirror = mirror
                    self._commitRegister('vlans')
            else:
                self.logger.error('vlanEdit: mirror needs to be an instance bool')
        if igmp is not None:
            if isinstance(igmp, bool):
                if not igmp == self.vlans[idx].igmp:
                    self.vlans[idx].igmp = igmp
                    self._commitRegister('vlans')
            else:
                self.logger.error('vlanEdit: igmp needs to be an instance bool')
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
                    self.logger.error(f'vlanAdd: vlan with id {vlan.id} allready present')
                    break
            else:
                self.vlans.append(vlan)
                self._commitRegister('vlans')
        elif isinstance(vlan, int):
            for v in self.vlans:
                if v.id == vlan:
                    self.logger.error(f'vlanAdd: vlan with id {vlan} allready present')
                    break
            else:
                v = SwitchVLAN()
                v.id = vlan
                self.vlans.append(v)
                self._commitRegister('vlans')
                self.vlanEdit(vlan, isolation=isolation, learning=learning, mirror=mirror, igmp=igmp, memberAdd=memberAdd, memberRemove=memberRemove)
        else:
            self.logger.error('vlanAdd: vlan needs to be an instance of int or SwitchVLAN')

    def vlanRemove(self, vlan):
        if isinstance(vlan, SwitchVLAN):
            vlan = vlan.id
        elif not isinstance(vlan, int):
            self.logger.error('vlanRemove: vlan needs to be an instance of int or SwitchVLAN')
        for idx in range(len(self.vlans)):
            if self.vlans[idx].id == vlan:
                self.vlans.removeIndex(idx)
                self._commitRegister('vlans')
                break
        else:
            self.logger.warning(f'vlanRemove: vlan with id {vlan} was not present')


class MikroTikSwitchCRS328(MikroTikSwitch):
    def loadPorts(self):
        self.ports = list()
        r = self.getData('link.b')
        for t in ['gbe'] * int(r.get('sfpo', '0'), 16) + ['sfp+'] * int(r.get('sfp', '0'), 16):
            p = SwitchPort()
            p.type = t
            self.ports.append(p)
        super().loadPorts(r)
        self._commitUnregister('ports')


model_mapping = {
    'generic': MikroTikSwitch,
    'CRS328-24P-4S+': MikroTikSwitchCRS328
}
