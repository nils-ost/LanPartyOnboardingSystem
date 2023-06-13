from elements._elementBase import ElementBase, docDB
from elements import Participant, Device


class Seat(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, default=1, notnone=True),
        pw=ElementBase.addAttr(type=str, default=None),
        table_id=ElementBase.addAttr(notnone=True, fk='Table')
    )

    def validate(self):
        errors = dict()
        if not docDB.exists('Table', self['table_id']):
            errors['table_id'] = {'code': 50, 'desc': f"There is no Table with id '{self['table_id']}'"}
        if self['number'] < 1:
            errors['number'] = {'code': 51, 'desc': 'needs to be 1 or bigger'}
        elif docDB.search_one(self.__class__.__name__, {'table_id': self['table_id'], 'number': self['number'], '_id': {'$ne': self['_id']}}) is not None:
            errors['number'] = {'code': 52, 'desc': 'needs to be unique per Table'}
        return errors

    def delete_post(self):
        for d in [Device(d) for d in docDB.search_many('Device', {'seat_id': self['_id']})]:
            d['seat_id'] = None
            d['participant_id'] = None
            d['ip_pool_id'] = None
            d['ip'] = None
            d.save()
        for p in [Participant(p) for p in docDB.search_many('Participant', {'seat_id': self['_id']})]:
            p['seat_id'] = None
            p.save()
