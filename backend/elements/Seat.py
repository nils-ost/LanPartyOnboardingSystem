from elements._elementBase import ElementBase, docDB
from elements import Participant, Device


class Seat(ElementBase):
    _attrdef = dict(
        number=ElementBase.addAttr(type=int, default=1, notnone=True),
        number_absolute=ElementBase.addAttr(type=int, default=None, unique=True),
        pw=ElementBase.addAttr(type=str, default=None),
        table_id=ElementBase.addAttr(notnone=True, fk='Table'),
        claiming_device_id=ElementBase.addAttr(type=str, fk='Device', default=None)
    )

    @classmethod
    def get_by_table(cls, table_id):
        result = list()
        for fromdb in docDB.search_many(cls.__name__, {'table_id': table_id}):
            r = cls()
            r._attr = fromdb
            result.append(r)
        return result

    @classmethod
    def get_by_number(cls, table_id, number):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'number': number, 'table_id': table_id})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_number_absolute(cls, number):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'number_absolute': number})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    @classmethod
    def get_by_claiming(cls, device_id):
        result = cls()
        fromdb = docDB.search_one(cls.__name__, {'claiming_device_id': device_id})
        if fromdb is not None:
            result._attr = fromdb
            return result
        return None

    def validate(self):
        errors = dict()
        if not docDB.exists('Table', self['table_id']):
            errors['table_id'] = {'code': 50, 'desc': f"There is no Table with id '{self['table_id']}'"}
        elif self['number'] < 1:
            errors['number'] = {'code': 51, 'desc': 'needs to be 1 or bigger'}
        elif docDB.search_one(self.__class__.__name__, {'table_id': self['table_id'], 'number': self['number'], '_id': {'$ne': self['_id']}}) is not None:
            errors['number'] = {'code': 52, 'desc': 'needs to be unique per Table'}
        elif (self.table().seat_ip_pool()['range_start'] + self['number'] - 1) > self.table().seat_ip_pool()['range_end']:
            errors['number'] = {'code': 54, 'desc': 'is exceeding Tables IpPool range'}
        if self['number_absolute'] is not None and self['number_absolute'] < 0:
            errors['number_absolute'] = {'code': 53, 'desc': 'needs to be 0 or bigger'}
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
