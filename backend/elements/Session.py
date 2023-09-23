from elements._elementBase import ElementBase, docDB
from helpers.client import get_client_ip
from datetime import datetime
import cherrypy


class Session(ElementBase):
    _attrdef = dict(
        till=ElementBase.addAttr(type=int, notnone=True),
        ip=ElementBase.addAttr(type=str, default=None, notnone=True),
        complete=ElementBase.addAttr(type=bool, default=False),
        participant_id=ElementBase.addAttr(notnone=True, fk='Participant')
    )

    def validate(self):
        errors = dict()
        if not docDB.exists('Participant', self['participant_id']):
            errors['participant_id'] = {'code': 80, 'desc': f"There is no Participant with id '{self['participant_id']}'"}
        if self['till'] <= int(datetime.now().timestamp()):
            errors['till'] = {'code': 81, 'desc': 'needs to be in the future'}
            self.delete()
        if cherrypy.request:
            if not self['ip'] == get_client_ip():
                errors['ip'] = {'code': 82, 'desc': 'does not match with the IP of request'}
                self.delete()
        return errors

    def delete_others(self):
        for sd in docDB.search_many('Session', {'participant_id': self['participant_id'], '_id': {'$ne': self['_id']}}):
            s = Session(sd)
            s.delete()

    def admin(self):
        p = docDB.get('Participant', self['participant_id'])
        if p is not None:
            return p.get('admin', False)
        return False
