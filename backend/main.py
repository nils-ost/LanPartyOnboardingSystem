import cherrypy
import cherrypy_cors
from helpers.docdb import docDB
from helpers.config import get_config
from helpers.elementendpoint import ElementEndpointBase
from elements import VLAN, Switch, IpPool

# logging.basicConfig(format='%(levelname)s:%(name)s:%(message)s', level='INFO')


class API():
    def __init__(self):
        self.vlan = VLANEndpoint()
        self.switch = SwitchEndpoint()
        self.ippool = IpPoolEndpoint()


class VLANEndpoint(ElementEndpointBase):
    _element = VLAN


class SwitchEndpoint(ElementEndpointBase):
    _element = Switch


class IpPoolEndpoint(ElementEndpointBase):
    _element = IpPool


if __name__ == '__main__':
    conf = {
    }
    config = get_config('server')
    cherrypy_cors.install()
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['port'], 'cors.expose.on': True})

    docDB.wait_for_connection()
    cherrypy.quickstart(API(), '/', conf)
