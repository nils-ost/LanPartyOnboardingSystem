from elements._elementBase import ElementBase, docDB


class Participant(ElementBase):
    _attrdef = dict(
        admin=ElementBase.addAttr(type=bool, default=False, notnone=True),
        name=ElementBase.addAttr(default='', notnone=True),
        login=ElementBase.addAttr(type=str, unique=True, default=None),
        pw=ElementBase.addAttr(type=str, default=None),
        seat_id=ElementBase.addAttr(type=str, unique=True)
    )

    def validate(self):
        errors = dict()
        if self['seat_id'] and not docDB.exists('Seat', self['seat_id']):
            errors['seat_id'] = f"There is no Seat with id '{self['seat_id']}'"
        return errors