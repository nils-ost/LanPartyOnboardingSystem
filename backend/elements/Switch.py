from elements._elementBase import ElementBase, docDB


class Switch(ElementBase):
    _attrdef = dict(
        addr=ElementBase.addAttr(unique=True, notnone=True),
        user=ElementBase.addAttr(default='', notnone=True),
        pw=ElementBase.addAttr(default='', notnone=True),
        purpose=ElementBase.addAttr(type=int, default=1, notnone=True),
        onboarding_vlan_id=ElementBase.addAttr(default=None)
    )

    def validate(self):
        errors = dict()
        if self['purpose'] not in range(3):
            errors['purpose'] = 'needs to be 0, 1 or 2'
        if self['purpose'] in range(1, 3):
            if self['onboarding_vlan_id'] is None:
                errors['onboarding_vlan_id'] = "can't be None for purposes 1 and 2"
            else:
                v = docDB.get('VLAN', self['onboarding_vlan_id'])
                if v is None:
                    errors['onboarding_vlan_id'] = f"There is no VLAN with id '{self['onboarding_vlan_id']}'"
                elif not v['purpose'] == 2:
                    errors['onboarding_vlan_id'] = f"VLAN purpose needs to be 2 (onboarding) but is '{v['purpose']}'"
                elif docDB.search_one(self.__class__.__name__, {'onboarding_vlan_id': self['onboarding_vlan_id'], '_id': {'$ne': self['_id']}}) is not None:
                    errors['onboarding_vlan_id'] = 'This VLAN is allready used on a switch as onboarding_vlan'
        return errors

    def save_pre(self):
        if self['purpose'] == 0:
            self['onboarding_vlan_id'] = None
