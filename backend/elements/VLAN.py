import os
from elements._elementBase import ElementBase, docDB


class VLAN(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, unique=True, notnone=True),
        purpose=ElementBase.addAttr(type=int, default=3, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True)
    )

    @classmethod
    def get_by_number(cls, number):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'number': number})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_purpose(cls, number):
        result = list()
        for fromdb in docDB.search_many(cls.__name__, {'purpose': number}):
            r = cls()
            r._attr = fromdb
            result.append(r)
        return result

    def validate(self):
        errors = dict()
        if self['number'] not in range(1, 1025):
            errors['number'] = {'code': 10, 'desc': 'needs to be a value from 1 to 1024'}
        if self['purpose'] not in range(4):
            errors['purpose'] = {'code': 11, 'desc': 'needs to be 0, 1, 2 or 3'}
        if self['purpose'] in range(2):
            found = docDB.search_one(self.__class__.__name__, {'_id': {'$ne': self['_id']}, 'purpose': self['purpose']})
            if found is not None:
                errors['purpose'] = {'code': 12, 'desc': f"values 0 and 1 need to be unique, but element with value {self['purpose']} allready present"}
        return errors

    def delete_pre(self):
        if docDB.search_one('IpPool', {'vlan_id': self['_id']}) is not None:
            return {'error': {'code': 1, 'desc': 'at least one IpPool is using this VLAN'}}
        if docDB.search_one('Switch', {'onboarding_vlan_id': self['_id']}) is not None:
            return {'error': {'code': 4, 'desc': 'at least one Switch is using this VLAN'}}
        from elements import Switch
        for switch in Switch.all():
            switch.remove_vlan(self['number'])

    def commit_os_interface(self):
        from elements import IpPool
        if self['purpose'] == 3:
            return 1  # does not get an interface
        if self['_id'] is None:
            return 2  # not saved yet, therefor could be invalid
        iname = docDB.get_setting('os_nw_interface')
        if iname is None:
            return 3  # maybe return an error
        netplan_path = docDB.get_setting('os_netplan_path')
        if netplan_path is None:
            return 4  # maybe return an error
        if self['purpose'] == 0:
            for pool in IpPool.get_by_vlan(self['_id']):
                if pool['lpos']:
                    break
            else:
                return 5  # no pool defined as lpos
        else:
            pool = IpPool.get_by_vlan(self['_id'])
            if len(pool) == 0:
                return 6  # no needed pool defined
            pool = pool[0]
        ip = '.'.join([str(e) for e in IpPool.int_to_octetts(pool['range_start'])])
        mask = pool['mask']
        cfg = f"""network:
  version: 2
  renderer: networkd
  vlans:
    vlan{self['number']}:
      id: {self['number']}
      link: {iname}
      addresses:
        - {ip}/{mask}
      dhcp4: no"""
        with open(os.path.join(netplan_path, f"02-vlan{self['number']}.yaml"), 'w') as f:
            f.write(cfg)
        return 0

    def retreat_os_interface(self):
        if self['purpose'] == 3:
            return 1  # does not got an interface
        if self['_id'] is None:
            return 2  # not saved yet, therefor could be invalid
        netplan_path = docDB.get_setting('os_netplan_path')
        if netplan_path is None:
            return 3  # maybe return an error
        os.remove(os.path.join(netplan_path, f"02-vlan{self['number']}.yaml"))
        return 0
