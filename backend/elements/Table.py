from elements._elementBase import ElementBase, docDB


class Table(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, unique=True, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        switch_id=ElementBase.addAttr(notnone=True),
        ip_pool_id=ElementBase.addAttr(unique=True, notnone=True)
    )

    def validate(self):
        errors = dict()
        switch = docDB.get('Switch', self['switch_id'])
        if self['number'] < 0:
            errors['number'] = 'needs to be bigger or equal to zero'
        if switch is None:
            errors['switch_id'] = f"There is no Switch with id '{self['switch_id']}'"
        elif switch['purpose'] not in range(1, 3):
            errors['switch_id'] = 'Purpose of Switch needs to be 1 or 2'
        pool = docDB.get('IpPool', self['ip_pool_id'])
        if pool is None:
            errors['ip_pool_id'] = f"There is no IpPool with id '{self['ip_pool_id']}'"
        elif not docDB.get('VLAN', pool['vlan_id'])['purpose'] == 0:
            errors['ip_pool_id'] = 'VLAN of IpPool needs to be of purpose 0 (play/seats)'
        return errors
