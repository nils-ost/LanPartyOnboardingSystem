from elements._elementBase import ElementBase, docDB


class Seat(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, default=1, notnone=True),
        pw=ElementBase.addAttr(type=str, default=None),
        table_id=ElementBase.addAttr(notnone=True)
    )

    def validate(self):
        errors = dict()
        if not docDB.exists('Table', self['table_id']):
            errors['table_id'] = f"There is no Table with id '{self['table_id']}'"
        if self['number'] < 1:
            errors['number'] = 'needs to be 1 or bigger'
        elif docDB.search_one(self.__class__.__name__, {'table_id': self['table_id'], 'number': self['number'], '_id': {'$ne': self['_id']}}) is not None:
            errors['number'] = 'needs to be unique per Table'
        return errors
