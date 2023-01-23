from elements._elementBase import ElementBase


class VLAN(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, unique=True, notnone=True),
        purpose=ElementBase.addAttr(type=int, default=0, notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True)
    )

    def validate(self):
        errors = dict()
        if self['number'] < 1:
            errors['number'] = "can't be smaller than 1"
        if self['number'] > 1024:
            errors['number'] = "can't be bigger than 1024"
        if self['purpose'] not in range(3):
            errors['purpose'] = 'needs to be 0, 1 or 2'
        return errors
