import cherrypy
import cherrypy_cors
from elements import Session
from helpers.system import get_commited, get_open_commits, get_use_absolute_seatnumbers
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
            if len(session.validate_base()) == 0 and session.admin:
                # these are for admins only
                result['commited'] = get_commited()
                result['open_commits'] = True if get_open_commits() > 0 else False

            result['seatnumbers_absolute'] = get_use_absolute_seatnumbers()
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
    def commit_dnsmasq(self):
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
            from helpers.vlanmgmt import vlan_dnsmasq_config_commit
            result = vlan_dnsmasq_config_commit()
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
    def retreat_dnsmasq(self):
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
            from helpers.vlanmgmt import vlan_dnsmasq_config_retreat
            result = vlan_dnsmasq_config_retreat()
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
    def absolute_seatnumbers(self):
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
            attr = cherrypy.request.json
            if 'enable' not in attr:
                cherrypy.response.status = 400
                return {'error': 'missing "enable" attribute in request'}
            from helpers.system import set_use_absolute_seatnumbers
            set_use_absolute_seatnumbers(bool(attr['enable']))
            cherrypy.response.status = 201
            return {'status': 'ok'}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
