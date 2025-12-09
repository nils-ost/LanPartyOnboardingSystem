from noapiframe.elements import SessionBase
from .Participant import Participant


class Session(SessionBase):
    cookie_name = 'LPOSsession'
    _user_cls = Participant
