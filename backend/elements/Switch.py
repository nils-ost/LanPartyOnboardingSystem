from elements._elementBase import ElementBase, docDB


class Switch(ElementBase):
    _attrdef = dict(
        addr=ElementBase.addAttr(unique=True, notnone=True),
        user=ElementBase.addAttr(default='', notnone=True),
        pw=ElementBase.addAttr(default='', notnone=True),
        purpose=ElementBase.addAttr(type=int, default=1, notnone=True),
        participant_vlan_id=ElementBase.addAttr(default=None)
    )

    def validate(self):
        errors = dict()
        if self['purpose'] not in range(3):
            errors['purpose'] = 'needs to be 0, 1 or 2'
        if self['participant_vlan_id'] is not None:
            v = docDB.get('VLAN', self['participant_vlan_id'])
            if v is None:
                errors['participant_vlan_id'] = f"There is no VLAN with id '{self['participant_vlan_id']}'"
            elif not v['purpose'] == 2:
                errors['participant_vlan_id'] = f"VLAN purpose needs to be 2 (onboarding) but is '{v['purpose']}'"
        return errors
