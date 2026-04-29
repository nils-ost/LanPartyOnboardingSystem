import requests
from requests.auth import HTTPDigestAuth
import logging
from .baseswitch import BaseSwitch
from .helpers import responseToJson, asciiToStr, jsonToRequest, strToAscii, translateKeys
from .parts import SwitchPort, SwitchVLAN


model_mapping = dict()


class AutoDetectSwitch(BaseSwitch):
    pass


class MikroTikSwitch(BaseSwitch):
    speed_mapping = {
        '0x00': '10M',
        '0x01': '100M',
        '0x02': '1G',
        '0x03': '10G',
        '0x07': None
    }
    vlan_mode_mapping = {
        '0x00': 'disabled',
        '0x01': 'optional',
        '0x02': 'enabled',
        '0x03': 'strict'
    }
    vlan_receive_mapping = {
        '0x00': 'any',
        '0x01': 'only tagged',
        '0x02': 'only untagged'
    }

    def __init__(self, host, user, password):
        super().__init__(host, user, password)
        self.logger = logging.getLogger('MikroTikSwitch')
        self.vendor = 'MikroTik'
        self.model = 'generic'
        self._conn = requests.session()
        self._conn.auth = HTTPDigestAuth(user, password)
        self.loadModel()

    def _getData(self, doc, toJson=True):
        try:
            url = f'http://{self._host}/{doc}'
            self.logger.debug(f'getData:{url}')
            r = self._conn.get(url, timeout=0.1)
            self.logger.debug(f'getData:{r.text}')
            self.connected = True
            if toJson:
                return responseToJson(r.text)
            return r.text
        except Exception as e:
            self.logger.debug(f'getData:exception:{repr(e)}')
            self.connected = False
            if toJson:
                return dict()
            return ''

    def _postData(self, doc, data):
        try:
            url = f'http://{self._host}/{doc}'
            data = jsonToRequest(data)
            self.logger.info(f'postData:{url}')
            self.logger.debug(f'postData:{data}')
            r = self._conn.post(url, data=data, timeout=0.2)
            self.logger.debug(f'postData:status_code:{r.status_code}')
            self.connected = True
        except Exception as e:
            self.logger.debug(f'postData:exception:{repr(e)}')
            self.connected = False

    def loadModel(self):
        r = self._getData('sys.b')
        if len(r) == 0:
            self.logger.error(f"loadModel ({self._host}): Couldn't fetch data")
            return

        model = r.get('brd')
        if model is None:
            model = r.get('i07')
        if model is None:
            model = ''
            self.logger.error(f"loadModel ({self._host}): Couldn't identify model")
        model = asciiToStr(model)

        if model not in model_mapping:
            self.logger.warning(f"loadModel ({self._host}): Model '{model}' not in mapping, falling back to 'generic'")
        if not model == self.model and model in model_mapping:
            self.model = model
            self.__class__ = model_mapping[model]
        self.loadAll()

    def loadSystem(self, response=None):
        """
        reads: id, mac, avln
        """
        if response is None:
            r = self._getData('sys.b')
            if len(r) == 0:
                self.logger.error(f"loadSystem ({self._host}): Couldn't fetch data")
                return
        else:
            r = response
        self.identity = asciiToStr(r.get('id', ''))
        self.mac_addr = r.get('mac', '')
        self.mgmt_vlan = int(r.get('avln', '0'), 16)
        if self.mgmt_vlan == 0:
            self.mgmt_vlan = None
        self._commitUnregister('system')

    def loadPorts(self, response=None):
        """
        reads: sfpo, prt
        """
        if response is None:
            self.ports = list()
            r = self._getData('link.b')
            for t in ['gbe'] * int(r.get('sfpo', '0'), 16):
                p = SwitchPort()
                p.type = t
                self.ports.append(p)
        else:
            r = response

        if not len(self.ports) == int(r.get('prt', '0'), 16):
            self.logger.error(f"loadPorts ({self._host}): Detected port-count doesn't match reported port-count")
        self.reloadPorts(r)
        self._commitUnregister('ports')

    def reloadPorts(self, response=None):
        """
        reads: lnk, en, nm, spd
        """
        if response is None:
            r = self._getData('link.b')
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
            if spd not in self.speed_mapping:
                self.logger.warning(f"loadPorts ({self._host}): Detected speed {spd} can't be found in speed_mapping, replacing it by None")
                spd = None
            else:
                spd = self.speed_mapping[spd]
            self.ports[idx].speed = spd
        self._commitUnregister('ports')

    def loadIsolation(self, response=None):
        """
        reads: fp*
        """
        if response is None:
            r = self._getData('fwd.b')
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

    def loadHosts(self, response=None):
        """
        reads: *(prt, adr)
        """
        if response is None:
            r = self._getData('!dhost.b')
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

    def loadVlans(self, response=None):
        """
        reads: *(vid, piso, lrn, mrr, igmp, mbr)
        """
        if response is None:
            r = self._getData('vlan.b')
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

    def loadPortsVlan(self, response=None):
        """
        reads: fvid, vlan, vlni, dvid
        """
        if response is None:
            r = self._getData('fwd.b')
        else:
            r = response
        fvid = bin(int(r.get('fvid', '0'), 16)).replace('0b', '')
        fvid = fvid[::-1] + '0' * (len(self.ports) - len(fvid))
        for idx in range(len(self.ports)):
            mode = r.get('vlan', list())[idx]
            if mode not in self.vlan_mode_mapping:
                self.logger.warning(f"loadPortsVlan ({self._host}): Detected vlan_mode {mode} can't be found in vlan_mode_mapping")
            else:
                self.ports[idx].vlan_mode = self.vlan_mode_mapping[mode]
            receive = r.get('vlni', list())[idx]
            if receive not in self.vlan_receive_mapping:
                self.logger.warning(f"loadPortsVlan ({self._host}): Detected vlan_receive {receive} can't be found in vlan_receive_mapping")
            else:
                self.ports[idx].vlan_receive = self.vlan_receive_mapping[receive]
            self.ports[idx].vlan_default = int(r.get('dvid', list())[idx], 16)
            self.ports[idx].vlan_force = fvid[idx] == '1'
        self._commitUnregister('portsvlan')

    def commitSystem(self, request=None):
        r = request if request else dict()
        if self.mgmt_vlan is None:
            r['avln'] = '0x00'
        else:
            avln = hex(self.mgmt_vlan).replace('0x', '')
            avln = '0x' + '0' * (len(avln) % 2) + avln
            r['avln'] = avln
        self._postData('sys.b', r)
        self._commitUnregister('system')

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
        self._postData('link.b', r)
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
        self._postData('fwd.b', r)
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
        self._postData('vlan.b', r)
        self._commitUnregister('vlans')

    def commitPortsVlan(self, request=None):
        r = request if request else dict()
        r['vlan'] = list()
        r['vlni'] = list()
        r['dvid'] = list()
        fvid = ''
        for port in self.ports:
            if port.vlan_mode not in self.vlan_mode_mapping_reverse:
                self.logger.error(
                    f'commitPortsVlan ({self._host}): vlan_mode {port.vlan_mode} of Port {port.idx} not found in vlan_mode_mapping_reverse. Assuming 0x02')
                r['vlan'].append('0x02')
            else:
                r['vlan'].append(self.vlan_mode_mapping_reverse[port.vlan_mode])
            if port.vlan_receive not in self.vlan_receive_mapping_reverse:
                msg = ' '.join([
                    f'commitPortsVlan ({self._host}): vlan_receive {port.vlan_receive} of Port {port.idx}',
                    'not found in vlan_receive_mapping_reverse. Assuming 0x02'])
                self.logger.error(msg)
                r['vlni'].append('0x02')
            else:
                r['vlni'].append(self.vlan_receive_mapping_reverse[port.vlan_receive])
            dvid = hex(port.vlan_default).replace('0x', '')
            r['dvid'].append('0x' + '0' * (len(dvid) % 2) + dvid)
            fvid += '1' if port.vlan_force else '0'
        fvid = hex(int(fvid[::-1], 2)).replace('0x', '')
        r['fvid'] = '0x' + '0' * (len(fvid) % 2) + fvid
        self._postData('fwd.b', r)
        self._commitUnregister('portsvlan')


class MikroTikSwitchCRS309(MikroTikSwitch):
    vlan_mode_mapping = {
        '0x00': 'disabled',
        '0x01': 'optional',
        '0x02': 'enabled'
    }
    vlan_mode_mapping_reverse = dict([(v, k) for k, v in vlan_mode_mapping.items()])

    speed_mapping = {
        '0x00': '10M',
        '0x01': '100M',
        '0x02': '1G',
        '0x03': '10G',
        '0x04': None
    }

    def loadPorts(self):
        self.ports = list()
        r = self._getData('link.b')
        for t in ['sfp+'] * int(r.get('sfp', '0'), 16) + ['gbe']:
            p = SwitchPort()
            p.type = t
            self.ports.append(p)
        super().loadPorts(r)
        self._commitUnregister('ports')


class MikroTikSwitchCRS328(MikroTikSwitch):
    def loadPorts(self):
        self.ports = list()
        r = self._getData('link.b')
        for t in ['gbe'] * int(r.get('sfpo', '0'), 16) + ['sfp+'] * int(r.get('sfp', '0'), 16):
            p = SwitchPort()
            p.type = t
            self.ports.append(p)
        super().loadPorts(r)
        self._commitUnregister('ports')


class MikroTikSwitchCSS318(MikroTikSwitch):
    def loadPorts(self):
        self.ports = list()
        r = self._getData('link.b')
        for t in ['gbe'] * int(r.get('sfpo', '0'), 16) + ['sfp+'] * int(r.get('sfp', '0'), 16):
            p = SwitchPort()
            p.type = t
            self.ports.append(p)
        super().loadPorts(r)
        self._commitUnregister('ports')


class MikroTikSwitchCSS326(MikroTikSwitch):
    def loadPorts(self):
        self.ports = list()
        r = self._getData('link.b')
        for t in ['gbe'] * int(r.get('sfpo', '0'), 16) + ['sfp+'] * int(r.get('sfp', '0'), 16):
            p = SwitchPort()
            p.type = t
            self.ports.append(p)
        super().loadPorts(r)
        self._commitUnregister('ports')


class MikroTikSwitchCSS610(MikroTikSwitch):
    vlan_mode_mapping = {
        '0x00': 'disabled',
        '0x01': 'optional',
        '0x02': 'strict'
    }
    vlan_mode_mapping_reverse = dict([(v, k) for k, v in vlan_mode_mapping.items()])

    _translations = {
        'sys.b': {'i07': 'brd', 'i05': 'id', 'i03': 'mac', 'i1b': 'avln'},
        'link.b': {'i0a': 'nm', 'i08': 'spd', 'i06': 'lnk', 'i01': 'en'},
        'fwd.b': {
            'i15': 'vlan', 'i17': 'vlni', 'i18': 'dvid', 'i19': 'fvid',
            'i01': 'fp1', 'i02': 'fp2', 'i03': 'fp3', 'i04': 'fp4', 'i05': 'fp5',
            'i06': 'fp6', 'i07': 'fp7', 'i08': 'fp8', 'i09': 'fp9', 'i0a': 'fp10'},
        '!dhost.b': {'i01': 'adr', 'i02': 'prt'},
        'vlan.b': {'i01': 'vid', 'i02': 'mbr', 'i03': 'igmp'},
        '!stats.b': {
            'i01': 'rb', 'i05': 'rup', 'i07': 'rbp', 'i08': 'rmp', 'i0f': 'tb',
            'i11': 'tup', 'i13': 'tmp', 'i14': 'tbp', 'i23': 'rtp', 'i24': 'ttp'}
    }

    def _getData(self, doc, toJson=True):
        r = super()._getData(doc, toJson)
        if not toJson:
            return r
        elif doc in self._translations:
            return translateKeys(r, self._translations[doc])
        else:
            return r

    def _postData(self, doc, data):
        if doc in self._translations:
            data = translateKeys(data, dict([(v, k) for k, v in self._translations[doc].items()]), ommit_surplus=True)
        super()._postData(doc=doc, data=data)

    def loadPorts(self):
        self.ports = list()
        r = self._getData('link.b')
        r['prt'] = '0x0a'  # hardcoded as this value seems not to come from switch
        r['sfpo'] = '0x08'  # hardcoded as this value seems not to come from switch
        r['sfp'] = '0x02'  # hardcoded as this value seems not to come from switch
        for t in ['gbe'] * int(r.get('sfpo', '0'), 16) + ['sfp+'] * int(r.get('sfp', '0'), 16):
            p = SwitchPort()
            p.type = t
            self.ports.append(p)
        super().loadPorts(r)
        self._commitUnregister('ports')

    def vlanEdit(self, vlan, isolation=None, learning=None, mirror=None, igmp=None, memberAdd=None, memberRemove=None):
        if isolation is not None:
            self.logger.warning(f'vlanEdit ({self._host}): switch-model does not support vlan-isolation')
        if learning is not None:
            self.logger.warning(f'vlanEdit ({self._host}): switch-model does not support vlan-learning')
        if mirror is not None:
            self.logger.warning(f'vlanEdit ({self._host}): switch-model does not support vlan-mirroring')
        super().vlanEdit(vlan=vlan, isolation=None, learning=None, mirror=None, igmp=igmp, memberAdd=memberAdd, memberRemove=memberRemove)


model_mapping = {
    'generic': MikroTikSwitch,
    'CRS309-1G-8S+': MikroTikSwitchCRS309,
    'CRS328-24P-4S+': MikroTikSwitchCRS328,
    'CSS318-16G-2S+': MikroTikSwitchCSS318,
    'CSS326-24G-2S+': MikroTikSwitchCSS326,
    'CSS610-8G-2S+': MikroTikSwitchCSS610
}
