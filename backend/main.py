import os
import cherrypy
import cherrypy_cors
import logging
from noapiframe import docDB, ElementEndpointBase
from noapiframe.endpoints import LoginEndpointBase, SettingEndpointBase
from helpers.backgroundworker import device_onboarding_start
from helpers.versioning import run as versioning_run
from endpoints import SystemEndpoint, SwitchEndpoint, OnboardingEndpoint, ParticipantEndpoint
from endpoints.metrics import start_metrics_exporter
from elements import Session, Setting, VLAN, IpPool, Table, Seat, Device, Port, PortConfigCache

logging.basicConfig(format='%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z', level='INFO')
logger = logging.getLogger('main')


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
        self.setting = SettingEndpoint()
        self.portconfigcache = PortConfigCacheEndpoint()


class LoginEndpoint(LoginEndpointBase):
    _session_cls = Session


class SettingEndpoint(SettingEndpointBase):
    _session_cls = Session
    _setting_cls = Setting
    _all_readable = ['domain', 'subdomain', 'absolute_seatnumbers', 'nlpt_sso', 'sso_login_url']
    _admin_writeable = ['os_nw_interface', 'play_dhcp', 'play_gateway', 'upstream_dns', 'domain', 'subdomain', 'absolute_seatnumbers', 'nlpt_sso',
                        'sso_ip_overwrite', 'sso_login_url', 'sso_onboarding_url', 'server_port', 'metrics_enabled', 'metrics_port',
                        'haproxy_api_host', 'haproxy_api_port', 'haproxy_api_user', 'haproxy_api_pw',
                        'play_vlan_def_ip', 'play_vlan_def_mask', 'mgmt_vlan_def_ip', 'mgmt_vlan_def_mask', 'ob_vlan_def_ip', 'ob_vlan_def_mask']


class VLANEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = VLAN


class IpPoolEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = IpPool


class TableEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = Table


class SeatEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = Seat


class DeviceEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = Device


class PortEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = Port
    _ro_attr = ['switchlink', 'number_display']


class PortConfigCacheEndpoint(ElementEndpointBase):
    _session_cls = Session
    _element = PortConfigCache
    _ro_all = True


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.staticdir.root': os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static'),
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ang/en',
            'tools.staticdir.index': 'index.html'
        },
        '/de': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ang/de',
            'tools.staticdir.index': 'index.html',
            'tools.staticdir.abs_index': True
        },
        '/en': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ang/en',
            'tools.staticdir.index': 'index.html',
            'tools.staticdir.abs_index': True
        }
    }
    listen_port = Setting.value('server_port')
    cherrypy_cors.install()
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': listen_port,
        'cors.expose.on': True,
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Access-Control-Allow-Origin', 'http://localhost:4200/'), ('Access-Control-Allow-Credentials', 'true')]})

    docDB.wait_for_connection()
    versioning_run()
    device_onboarding_start()
    start_metrics_exporter()

    try:
        from helpers.system import check_integrity
        from helpers.vlanmgmt import vlan_os_interfaces_commit, vlan_dns_server_commit, vlan_dhcp_server_commit
        from helpers.haproxy import ssoHAproxy, lposHAproxy
        if not check_integrity().get('code', 1) == 0:
            raise Exception('integrity check failed')
        if not vlan_os_interfaces_commit().get('code', 1) == 0:
            raise Exception('vlan os interfaces commit failed')
        if not vlan_dns_server_commit().get('code', 1) == 0:
            raise Exception('vlan dns server commit failed')
        if not vlan_dhcp_server_commit().get('code', 1) == 0:
            raise Exception('vlan dhcp server commit failed')
        if Setting.value('nlpt_sso'):
            ssoHAproxy.start_container()
            ssoHAproxy.wait_for_running()
            ssoHAproxy.setup_sso_ip()
        lposHAproxy.set_ms_redirect_url()
        logger.info('StartUp auto commit: finished')
    except Exception as e:
        logger.info(f'StartUp auto commit: {e}')

    cherrypy.quickstart(API(), '/', conf)
