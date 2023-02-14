import cherrypy
import cherrypy_cors
from helpers.docdb import docDB
from helpers.config import get_config
from endpoints.element import ElementEndpointBase
from endpoints.login import LoginEndpoint
from elements import VLAN, Switch, IpPool, Table, Seat, Participant, Device

# logging.basicConfig(format='%(levelname)s:%(name)s:%(message)s', level='INFO')


class API():
    def __init__(self):
        self.vlan = VLANEndpoint()
        self.switch = SwitchEndpoint()
        self.ippool = IpPoolEndpoint()
        self.table = TableEndpoint()
        self.seat = SeatEndpoint()
        self.participant = ParticipantEndpoint()
        self.device = DeviceEndpoint()
        self.login = LoginEndpoint()


class VLANEndpoint(ElementEndpointBase):
    _element = VLAN


class SwitchEndpoint(ElementEndpointBase):
    _element = Switch


class IpPoolEndpoint(ElementEndpointBase):
    _element = IpPool


class TableEndpoint(ElementEndpointBase):
    _element = Table


class SeatEndpoint(ElementEndpointBase):
    _element = Seat


class ParticipantEndpoint(ElementEndpointBase):
    _element = Participant


class DeviceEndpoint(ElementEndpointBase):
    _element = Device


if __name__ == '__main__':
    conf = {
    }
    config = get_config('server')
    cherrypy_cors.install()
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['port'], 'cors.expose.on': True})

    docDB.wait_for_connection()
    cherrypy.quickstart(API(), '/', conf)
