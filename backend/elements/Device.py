from elements._elementBase import ElementBase


class Device(ElementBase):
    _attrdef = dict(
        mac=ElementBase.addAttr(notnone=True),
        desc=ElementBase.addAttr(default='', notnone=True),
        seat_id=ElementBase.addAttr(),
        participant_id=ElementBase.addAttr(),
        ip_pool_id=ElementBase.addAttr(),
        ip=ElementBase.addAttr(type=int, unique=True)
    )

    def validate(self):
        errors = dict()
        return errors
