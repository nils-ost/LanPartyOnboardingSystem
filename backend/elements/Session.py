from elements._elementBase import ElementBase, docDB
from datetime import datetime


class Session(ElementBase):
    _attrdef = dict(
        till=ElementBase.addAttr(type=int, notnone=True),
        ip=ElementBase.addAttr(type=str, default=None, notnone=True),
        participant_id=ElementBase.addAttr(notnone=True)
    )

    def validate(self):
        errors = dict()
        if not docDB.exists('Participant', self['participant_id']):
            errors['participant_id'] = f"There is no Participant with id '{self['participant_id']}'"
        if self['till'] <= int(datetime.now().timestamp()):
            errors['till'] = 'needs to be in the future'
            self.delete()
        return errors
