from elements._elementBase import ElementBase, docDB


class Table(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, unique=True, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        switch_id=ElementBase.addAttr(notnone=True),
        seat_ip_pool_id=ElementBase.addAttr(unique=True, notnone=True),
        add_ip_pool_id=ElementBase.addAttr(notnone=True)
    )

    def validate(self):
        errors = dict()
        switch = docDB.get('Switch', self['switch_id'])
        if self['number'] < 0:
            errors['number'] = {'code': 40, 'desc': 'needs to be bigger or equal to zero'}
        if switch is None:
            errors['switch_id'] = {'code': 41, 'desc': f"There is no Switch with id '{self['switch_id']}'"}
        elif switch['purpose'] not in range(1, 3):
            errors['switch_id'] = {'code': 42, 'desc': 'Purpose of Switch needs to be 1 or 2'}
        seat_pool = docDB.get('IpPool', self['seat_ip_pool_id'])
        if seat_pool is None:
            errors['seat_ip_pool_id'] = {'code': 41, 'desc': f"There is no IpPool with id '{self['seat_ip_pool_id']}'"}
        elif not docDB.get('VLAN', seat_pool['vlan_id'])['purpose'] == 0:
            errors['seat_ip_pool_id'] = {'code': 43, 'desc': 'VLAN of IpPool needs to be of purpose 0 (play/seats)'}
        elif docDB.search_one(self.__class__.__name__, {'add_ip_pool_id': self['seat_ip_pool_id']}) is not None:
            errors['seat_ip_pool_id'] = {'code': 44, 'desc': 'allready in use as add_ip_pool_id on different Table'}
        add_pool = docDB.get('IpPool', self['add_ip_pool_id'])
        if add_pool is None:
            errors['add_ip_pool_id'] = {'code': 41, 'desc': f"There is no IpPool with id '{self['add_ip_pool_id']}'"}
        elif not docDB.get('VLAN', add_pool['vlan_id'])['purpose'] == 0:
            errors['add_ip_pool_id'] = {'code': 43, 'desc': 'VLAN of IpPool needs to be of purpose 0 (play/seats)'}
        elif docDB.search_one(self.__class__.__name__, {'seat_ip_pool_id': self['add_ip_pool_id']}) is not None:
            errors['add_ip_pool_id'] = {'code': 46, 'desc': 'allready in use as seat_ip_pool_id on different Table'}
        if self['seat_ip_pool_id'] == self['add_ip_pool_id']:
            errors['seat_ip_pool_id'] = {'code': 45, 'desc': "can't be the same as add_ip_pool_id"}
            errors['add_ip_pool_id'] = {'code': 45, 'desc': "can't be the same as seat_ip_pool_id"}
        return errors

    def delete_pre(self):
        if docDB.search_one('Seat', {'table_id': self['_id']}) is not None:
            return {'error': {'code': 3, 'desc': 'at least one Seat is using this Table'}}
