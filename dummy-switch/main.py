import cherrypy
import cherrypy_cors


hosts = [
    {'port': 0, 'addr': '001122334455'},
    {'port': 1, 'addr': '001122334466'},
    {'port': 5, 'addr': '001122334477'},
    {'port': 5, 'addr': '001122334488'},
    {'port': 8, 'addr': '001122334499'},
]

system = {
    'model': 'nils_ost - dummy switch',
    'identity': 'dummy1',
    'mac_addr': '112233445566',
    'mgmt_vlan': 0
}

ports = {
    'gbe-count': 8,
    'sfp-count': 2,
    'total-count': 10,
    'config': [
        {'idx': 0, 'en': True, 'link': True, 'name': 'Port1', 'spd': '1G'},
        {'idx': 1, 'en': True, 'link': True, 'name': 'Port2', 'spd': '1G'},
        {'idx': 2, 'en': True, 'link': False, 'name': 'Port3', 'spd': '1G'},
        {'idx': 3, 'en': True, 'link': False, 'name': 'Port4', 'spd': '1G'},
        {'idx': 4, 'en': True, 'link': False, 'name': 'Port5', 'spd': '1G'},
        {'idx': 5, 'en': True, 'link': True, 'name': 'Port6', 'spd': '1G'},
        {'idx': 6, 'en': True, 'link': False, 'name': 'Port7', 'spd': '1G'},
        {'idx': 7, 'en': True, 'link': False, 'name': 'Port8', 'spd': '1G'},
        {'idx': 8, 'en': True, 'link': True, 'name': 'SFP+1', 'spd': '10G'},
        {'idx': 9, 'en': True, 'link': False, 'name': 'SFP+2', 'spd': '10G'},
    ]
}

forward = {
    'from0': '0b0111111111',
    'from1': '0b1011111111',
    'from2': '0b1101111111',
    'from3': '0b1110111111',
    'from4': '0b1111011111',
    'from5': '0b1111101111',
    'from6': '0b1111110111',
    'from7': '0b1111111011',
    'from8': '0b1111111101',
    'from9': '0b1111111110',
}

vlans = [
    {'id': 1, 'isolation': True, 'learning': True, 'mirror': False, 'igmp': False, 'member': '0b1111111111'}
]

ports_vlans = {
    'idx0': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx1': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx2': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx3': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx4': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx5': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx6': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx7': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx8': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
    'idx9': {'mode': 'optional', 'receive': 'only untagged', 'default': '1', 'force': False},
}


class API():
    def __init__(self):
        self.system = SystemEndpoint()
        self.vlans = VlansEndpoint()
        self.ports = PortsEndpoint()
        self.ports_vlans = PortsVlansEndpoint()
        self.isolation = IsolationEndpoint()
        self.hosts = HostsEndpoint()

    @cherrypy.expose()
    def index(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy_cors.preflight(allowed_methods=['GET'])
            return
        elif cherrypy.request.method == 'GET':
            return 'nils_ost - dummy switch'


class SystemEndpoint(object):
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        global system
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
            return
        elif cherrypy.request.method == 'GET':
            return system
        elif cherrypy.request.method == 'POST':
            attr = cherrypy.request.json
            if 'mgmt_vlan' in attr:
                system['mgmt_vlan'] = attr['mgmt_vlan']


class VlansEndpoint(object):
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        global vlans
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
            return
        elif cherrypy.request.method == 'GET':
            return vlans
        elif cherrypy.request.method == 'POST':
            vlans = cherrypy.request.json


class PortsEndpoint(object):
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        global ports
        global hosts
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
            return
        elif cherrypy.request.method == 'GET':
            return ports
        elif cherrypy.request.method == 'POST':
            for p in cherrypy.request.json:
                for port in ports['config']:
                    if p.get('idx', 0) == port['idx']:
                        port['en'] = p.get('en', True)
                        port['name'] = p.get('name', '')
                        if not port['en']:
                            port['link'] = False  # disabled ports do not have link ...
                            new_hosts = list()  # ... or hosts attached
                            for host in hosts:
                                if host['port'] == port['idx']:
                                    continue
                                new_hosts.append(host)
                            hosts = new_hosts
                        continue


class PortsVlansEndpoint(object):
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        global ports_vlans
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
            return
        elif cherrypy.request.method == 'GET':
            return ports_vlans
        elif cherrypy.request.method == 'POST':
            ports_vlans = cherrypy.request.json


class IsolationEndpoint(object):
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        global forward
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
            return
        elif cherrypy.request.method == 'GET':
            return forward
        elif cherrypy.request.method == 'POST':
            forward = cherrypy.request.json


class HostsEndpoint(object):
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        global hosts
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy_cors.preflight(allowed_methods=['GET'])
            return
        elif cherrypy.request.method == 'GET':
            return hosts


if __name__ == '__main__':
    conf = {}
    listen_port = 1337  # ;)
    cherrypy_cors.install()
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': listen_port,
        'cors.expose.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Access-Control-Allow-Origin', '*'), ('Access-Control-Allow-Credentials', 'true')]})

    # TODO: init structure of dummy switch

    cherrypy.quickstart(API(), '/', conf)
