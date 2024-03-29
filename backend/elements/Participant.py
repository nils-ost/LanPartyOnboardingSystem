from elements._elementBase import ElementBase, docDB
from elements import Session, Device


class Participant(ElementBase):
    _attrdef = dict(
        admin=ElementBase.addAttr(type=bool, default=False, notnone=True),
        name=ElementBase.addAttr(default='', notnone=True),
        login=ElementBase.addAttr(type=str, unique=True, default=None),
        pw=ElementBase.addAttr(type=str, default=None),
        seat_id=ElementBase.addAttr(type=str, unique=True, fk='Seat')
    )

    def validate(self):
        errors = dict()
        if self['seat_id'] and not docDB.exists('Seat', self['seat_id']):
            errors['seat_id'] = {'code': 70, 'desc': f"There is no Seat with id '{self['seat_id']}'"}
        return errors

    @classmethod
    def get_by_login(cls, login):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'login': login})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_seat(cls, seat_id):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'seat_id': seat_id})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    def delete_post(self):
        for s in [Session(s) for s in docDB.search_many('Session', {'participant_id': self['_id']})]:
            s.delete()
        for d in [Device(d) for d in docDB.search_many('Device', {'participant_id': self['_id']})]:
            d['participant_id'] = None
            d['ip_pool_id'] = None
            d['ip'] = None
            d.save()
