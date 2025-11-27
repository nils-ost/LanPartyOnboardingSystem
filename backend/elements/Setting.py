from elements._elementBase import ElementBase, docDB


class Setting(ElementBase):
    _attrdef = dict(
        type=ElementBase.addAttr(default='str', notnone=True),
        value=ElementBase.addAttr(type=object, default=None),
        desc=ElementBase.addAttr(default='', notnone=True)
    )

    _valid_types = {
        'str': str,
        'int': int,
        'float': float,
        'bool': bool
    }

    _defaults = {
        'version':               {'type': 'str',   'value': None,        'desc': 'Running version of LPOS'},
        'server_port':           {'type': 'int',   'value': 8000,        'desc': 'Port the Backend should be listening on'},
        'metrics_enabled':       {'type': 'bool',  'value': False,       'desc': 'Whether to start the Metrics-Endpoint or not'},
        'metrics_port':          {'type': 'int',   'value': 8001,        'desc': 'Port that should be used for Metrics-Endpoint'},
        'haproxy_api_host':      {'type': 'str',   'value': '127.0.0.1', 'desc': 'IP or DNS where inbound haproxy API can be reached'},
        'haproxy_api_port':      {'type': 'int',   'value': 5555,        'desc': 'Port where inbound haproxy API can be reached'},
        'haproxy_api_user':      {'type': 'str',   'value': 'admin',     'desc': 'Username used to login to haproxy API'},
        'haproxy_api_pw':        {'type': 'str',   'value': 'adminpwd',  'desc': 'Password used to login to haproxy API'},
        'system_commited':       {'type': 'bool',  'value': False,       'desc': 'Indicates whether all parts of the system are commited'},
        'os_nw_interface':       {'type': 'str',   'value': '',          'desc': 'Identifier of Network-Interface to attach LPOS-VLANs to'},
        'play_dhcp':             {'type': 'str',   'value': '',          'desc': "IP used for LPOS's DHCP-Server in the Play-Network"},
        'play_gateway':          {'type': 'str',   'value': '',
                                  'desc': 'IP of the Gateway/Router in Play-Network, that is promoted to the Participants'},
        'upstream_dns':          {'type': 'str',   'value': '',          'desc': 'DNS Server that is promoted to the Participants'},
        'domain':                {'type': 'str',   'value': '',          'desc': '(Search-)Domain used in the Play-Network'},
        'subdomain':             {'type': 'str',   'value': '',          'desc': 'Subdomain used for presenting LPOS, Domain is extended to this string'},
        'absolute_seatnumbers':  {'type': 'bool',  'value': False,       'desc': 'Whether to use absolute numbering for Seats'},
        'nlpt_sso':              {'type': 'bool',  'value': False,
                                  'desc': 'Whether to use nlpt.online login for onboarding, or lokal onboarding credentials'},
        'sso_login_url':         {'type': 'str',   'value': '',          'desc': 'URL to receive SSO-User-Login token from external system'},
        'sso_onboarding_url':    {'type': 'str',   'value': '',          'desc': 'URL to receive SSO-onboarding information from external system'},
        'play_vlan_def_ip':      {'type': 'int',   'value': None,        'desc': 'default network IP used for new IpPools in play VLAN'},
        'play_vlan_def_mask':    {'type': 'int',   'value': 24,          'desc': 'default network mask used for new IpPools in play VLAN'},
        'mgmt_vlan_def_ip':      {'type': 'int',   'value': None,        'desc': 'default network IP used for new IpPools in mgmt VLAN'},
        'mgmt_vlan_def_mask':    {'type': 'int',   'value': 24,          'desc': 'default network mask used for new IpPools in mgmt VLAN'},
        'ob_vlan_def_ip':        {'type': 'int',   'value': None,        'desc': 'default network IP used for new IpPools in onboarding VLANs'},
        'ob_vlan_def_mask':      {'type': 'int',   'value': 24,          'desc': 'default network mask used for new IpPools in onboarding VLANs'},
        'integrity_switchlinks': {'type': 'float', 'value': 0.0,         'desc': 'Timestamp of last successful switchlinks integrity-check'},
        'integrity_vlans':       {'type': 'float', 'value': 0.0,         'desc': 'Timestamp of last successful vlans integrity-check'},
        'integrity_ippools':     {'type': 'float', 'value': 0.0,         'desc': 'Timestamp of last successful ippools integrity-check'},
        'integrity_tables':      {'type': 'float', 'value': 0.0,         'desc': 'Timestamp of last successful tables integrity-check'},
        'integrity_lpos':        {'type': 'float', 'value': 0.0,         'desc': 'Timestamp of last successful lpos integrity-check'},
        'integrity_settings':    {'type': 'float', 'value': 0.0,         'desc': 'Timestamp of last successful settings integrity-check'}
    }

    @classmethod
    def all(cls):
        result = list()
        keys = list()
        for element in docDB.search_many(cls.__name__, {}):
            result.append(cls(element))
            keys.append(element['_id'])
        for k in cls._defaults.keys():
            if k not in keys:
                result.append(cls.get(k))
        return result

    @classmethod
    def get(cls, id):
        result = cls()
        result._attr['_id'] = id
        fromdb = docDB.get(cls.__name__, id)
        if fromdb is not None:
            result._attr = fromdb
        elif id in cls._defaults:
            result._attr = cls._defaults[id]
            result._attr['_id'] = id
        return result

    @classmethod
    def value(cls, key):
        c = cls.get(key)
        if c is None:
            return None
        else:
            return c['value']

    @classmethod
    def set(cls, key, value):
        c = cls.get(key)
        if c is None:
            attr = dict()
            if key in cls._defaults:
                attr = cls._defaults[key]
            c = cls(attr)
        c['_id'] = key
        c['value'] = value
        return c.save()

    def validate(self):
        errors = dict()
        if self['type'] not in self._valid_types.keys():
            errors['type'] = {'code': 100, 'desc': f'needs to be one of: {list(self._valid_types.keys())}'}
        elif not isinstance(self['value'], self._valid_types[self['type']]) and self['value'] is not None:
            errors['value'] = {'code': 3, 'desc': f"needs to be of type {self._valid_types[self['type']]} or None"}
        return errors

    def save_pre(self):
        if self['_id'] in self._defaults:
            self['desc'] = self._defaults[self['_id']]['desc']
