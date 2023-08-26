from elements._elementBase import ElementBase, docDB


class IpPool(ElementBase):
    _attrdef = dict(
        desc=ElementBase.addAttr(default='', notnone=True),
        mask=ElementBase.addAttr(type=int, default=24, notnone=True),
        range_start=ElementBase.addAttr(type=int, notnone=True),
        range_end=ElementBase.addAttr(type=int, notnone=True),
        lpos=ElementBase.addAttr(type=bool, default=False, notnone=True),
        vlan_id=ElementBase.addAttr(notnone=True, fk='VLAN')
    )

    @classmethod
    def get_by_vlan(cls, vlan_id):
        result = list()
        for fromdb in docDB.search_many(cls.__name__, {'vlan_id': vlan_id}):
            r = cls()
            r._attr = fromdb
            result.append(r)
        return result

    def octetts_to_int(oct1, oct2, oct3, oct4):
        r = list()
        r.append(hex(oct1).replace('0x', ''))
        r.append(hex(oct2).replace('0x', ''))
        r.append(hex(oct3).replace('0x', ''))
        r.append(hex(oct4).replace('0x', ''))
        for idx in range(4):
            if len(r[idx]) < 2:
                r[idx] = '0' + r[idx]
        return int(''.join(r), 16)

    def int_to_octetts(input):
        h = hex(input).replace('0x', '')
        while len(h) < 8:
            h = '0' + h
        r = list()
        for idx in range(4):
            r.append(int(h[idx * 2:(idx + 1) * 2], 16))
        return tuple(r)

    def validate(self):
        from elements import VLAN
        errors = dict()
        if self['mask'] not in range(8, 31):
            errors['mask'] = {'code': 30, 'desc': 'needs to be between 8 and 30'}
        else:
            mask = int('1' * self['mask'] + '0' * (32 - self['mask']), 2)
            if not (self['range_start'] & mask) == (self['range_end'] & mask):
                errors['mask'] = {'code': 31, 'desc': 'does not fit to range_start and range_end'}
        if not self['range_end'] >= self['range_start']:
            errors['range_start'] = {'code': 32, 'desc': 'range_start needs to be smaller than or equal to range_end'}
            errors['range_end'] = {'code': 32, 'desc': 'range_start needs to be smaller than or equal to range_end'}
        elif self['lpos'] and not self['range_start'] == self['range_end']:
            errors['range_start'] = {'code': 38, 'desc': 'range_start and range_end need to be equal'}
            errors['range_end'] = {'code': 38, 'desc': 'range_start and range_end need to be equal'}
        else:
            if docDB.search_one(self.__class__.__name__, {
                    'range_start': {'$lte': self['range_end']}, 'range_end': {'$gte': self['range_end']}, '_id': {'$ne': self['_id']}}):
                errors['range_end'] = {'code': 33, 'desc': 'overlaps with existing IpPool'}
            if docDB.search_one(self.__class__.__name__, {
                    'range_start': {'$lte': self['range_start']}, 'range_end': {'$gte': self['range_start']}, '_id': {'$ne': self['_id']}}):
                errors['range_start'] = {'code': 33, 'desc': 'overlaps with existing IpPool'}
        if self['range_start'] < int('01000000', 16) or self['range_start'] > int('FFFFFFFD', 16):
            errors['range_start'] = {'code': 34, 'desc': 'not a valid IP'}
        if self['range_end'] < int('01000001', 16) or self['range_end'] > int('FFFFFFFE', 16):
            errors['range_end'] = {'code': 34, 'desc': 'not a valid IP'}
        if self['vlan_id']:
            vlan = VLAN.get(self['vlan_id'])
            if vlan is None:
                errors['vlan_id'] = {'code': 35, 'desc': f"There is no VLAN with id '{self['vlan_id']}'"}
            elif self['lpos'] and not vlan['purpose'] == 0:
                errors['vlan_id'] = {'code': 37, 'desc': 'Purpose of VLAN needs to be 0 (play)'}
            elif vlan['purpose'] in [1, 2] and docDB.search_one(self.__class__.__name__, {'vlan_id': self['vlan_id'], '_id': {'$ne': self['_id']}}):
                errors['vlan_id'] = {'code': 39, 'desc': f"Only one IpPool for VLAN with purpose of '{vlan['purpose']}' is allowed"}
        if self['lpos'] and docDB.search_one(self.__class__.__name__, {'lpos': True, '_id': {'$ne': self['_id']}}):
            errors['lpos'] = {'code': 36, 'desc': 'Only allowed once'}
        return errors

    def delete_pre(self):
        if docDB.search_one('Table', {'seat_ip_pool_id': self['_id']}) is not None:
            return {'error': {'code': 2, 'desc': 'at least one Table is using this IpPool'}}
        if docDB.search_one('Table', {'add_ip_pool_id': self['_id']}) is not None:
            return {'error': {'code': 2, 'desc': 'at least one Table is using this IpPool'}}

    def delete_post(self):
        from elements import Device
        for d in [Device(d) for d in docDB.search_many('Device', {'ip_pool_id': self['_id']})]:
            d['ip_pool_id'] = None
            d['ip'] = None
            d.save()
