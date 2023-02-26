from elements._elementBase import ElementBase, docDB


class VLAN(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, unique=True, notnone=True),
        purpose=ElementBase.addAttr(type=int, default=3, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True)
    )

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

    def delete_post(self):
        docDB.update_many('Switch', {'onboarding_vlan_id': self['_id']}, {'$set': {'onboarding_vlan_id': None}})
