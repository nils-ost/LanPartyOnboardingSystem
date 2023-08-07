import cherrypy
import cherrypy_cors
import logging
from helpers.docdb import docDB
from helpers.config import get_config
from helpers.backgroundworker import device_scanner
from threading import Thread
from endpoints import ElementEndpointBase, LoginEndpoint, SystemEndpoint, SwitchEndpoint, OnboardingEndpoint
from elements import VLAN, IpPool, Table, Seat, Participant, Device, Port

logging.basicConfig(format='%(levelname)s:%(name)s:%(message)s', level='INFO')


class API():
    def __init__(self):
        self.vlan = VLANEndpoint()
        self.switch = SwitchEndpoint()
        self.ippool = IpPoolEndpoint()
        self.table = TableEndpoint()
        self.seat = SeatEndpoint()
        self.participant = ParticipantEndpoint()
        self.device = DeviceEndpoint()
        self.port = PortEndpoint()
        self.login = LoginEndpoint()
        self.system = SystemEndpoint()
        self.onboarding = OnboardingEndpoint()


class VLANEndpoint(ElementEndpointBase):
    _element = VLAN


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


class PortEndpoint(ElementEndpointBase):
    _element = Port
    _ro_attr = ['switchlink']


if __name__ == '__main__':
    conf = {
    }
    config = get_config('server')
    cherrypy_cors.install()
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': config['port'],
        'cors.expose.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Access-Control-Allow-Origin', 'http://localhost:4200/'), ('Access-Control-Allow-Credentials', 'true')]})

    docDB.wait_for_connection()
    device_scanner_thread = Thread(target=device_scanner, daemon=True)
    device_scanner_thread.start()
    cherrypy.quickstart(API(), '/', conf)
