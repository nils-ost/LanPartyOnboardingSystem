import cherrypy
import cherrypy_cors
from elements import Session
from helpers.system import get_open_commits
from elements import Setting
from helpers.version import version


class SystemEndpoint():
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy_cors.preflight(allowed_methods=['GET'])
            return
        elif cherrypy.request.method == 'GET':
            result = dict()

            cookie = cherrypy.request.cookie.get('LPOSsession')
            if cookie:
                session = Session.get(cookie.value)
            else:
                session = Session.get(None)
            if len(session.validate_base()) == 0 and session.admin():
                # these are for admins only
                result['commited'] = Setting.value('system_commited')
                result['open_commits'] = True if get_open_commits() > 0 else False

            result['seatnumbers_absolute'] = Setting.value('absolute_seatnumbers')
            result['nlpt_sso'] = Setting.value('nlpt_sso')
            result['version'] = version
            return result
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def integrity(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy_cors.preflight(allowed_methods=['GET'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'GET':
            from helpers.system import check_integrity
            result = check_integrity()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit_interfaces(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.vlanmgmt import vlan_os_interfaces_commit
            result = vlan_os_interfaces_commit()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def retreat_interfaces(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.vlanmgmt import vlan_os_interfaces_retreat
            result = vlan_os_interfaces_retreat()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit_dns_servers(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.vlanmgmt import vlan_dns_server_commit
            result = vlan_dns_server_commit()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def retreat_dns_servers(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.vlanmgmt import vlan_dns_server_retreat
            result = vlan_dns_server_retreat()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit_dhcp_servers(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.vlanmgmt import vlan_dhcp_server_commit
            result = vlan_dhcp_server_commit()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def retreat_dhcp_servers(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.vlanmgmt import vlan_dhcp_server_retreat
            result = vlan_dhcp_server_retreat()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit_switches(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.switchmgmt import switches_commit
            result = switches_commit()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def retreat_switches(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.switchmgmt import switches_retreat
            result = switches_retreat()
            if result.get('code', 1) == 0:
                cherrypy.response.status = 201
                return result
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit_haproxy(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.system import check_integrity_haproxy_commit
            result = check_integrity_haproxy_commit()
            if result.get('code', 1) == 0:
                from helpers.haproxy import ssoHAproxy, lposHAproxy
                if Setting.value('nlpt_sso'):
                    ssoHAproxy.start_container()
                    ssoHAproxy.wait_for_running()
                    ssoHAproxy.setup_sso_ip()
                lposHAproxy.set_ms_redirect_url()
                cherrypy.response.status = 201
                return {'code': 0, 'desc': 'done'}
            else:
                cherrypy.response.status = 400
                return {'error': result}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def remove_offline_devices(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            from helpers.system import remove_offline_devices
            deleted_count = remove_offline_devices()
            cherrypy.response.status = 201
            return {'code': 0, 'desc': 'done', 'count': deleted_count}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
