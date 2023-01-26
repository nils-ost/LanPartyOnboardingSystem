from elements._elementBase import ElementBase, docDB


class IpPool(ElementBase):
    _attrdef = dict(
        purpose=ElementBase.addAttr(type=int, default=0, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        mask=ElementBase.addAttr(type=int, default=24, notnone=True),
        range_start=ElementBase.addAttr(type=int, notnone=True),
        range_end=ElementBase.addAttr(type=int, notnone=True),
        vlan_id=ElementBase.addAttr(notnone=True)
    )

    def validate(self):
        errors = dict()
        if self['purpose'] not in range(4):
            errors['purpose'] = 'needs to be 0, 1, 2 or 4'
        if self['mask'] not in range(8, 31):
            errors['mask'] = 'needs to be between 8 and 30'
        else:
            mask = int('1' * self['mask'] + '0' * (32 - self['mask']), 2)
            if not (self['range_start'] & mask) == (self['range_end'] & mask):
                errors['mask'] = 'does not fit to range_start and range_end'
        if not self['range_end'] > self['range_start']:
            errors['range_start'] = 'needs to be smaller than range_end'
            errors['range_end'] = 'needs to be bigger than range_start'
        else:
            if docDB.search_one(self.__class__.__name__, {
                    'range_start': {'$lte': self['range_end']}, 'range_end': {'$gte': self['range_end']}, '_id': {'$ne': self['_id']}}):
                errors['range_end'] = 'overlaps with existing IpPool'
            if docDB.search_one(self.__class__.__name__, {
                    'range_start': {'$lte': self['range_start']}, 'range_end': {'$gte': self['range_start']}, '_id': {'$ne': self['_id']}}):
                errors['range_start'] = 'overlaps with existing IpPool'
        if self['range_start'] < int('01000000', 16) or self['range_start'] > int('FFFFFFFD', 16):
            errors['range_start'] = 'not a valid IP'
        if self['range_end'] < int('01000001', 16) or self['range_end'] > int('FFFFFFFE', 16):
            errors['range_end'] = 'not a valid IP'
        if self['vlan_id'] and not docDB.exists('VLAN', self['vlan_id']):
            errors['vlan_id'] = f"There is no VLAN with id '{self['vlan_id']}'"
        return errors
