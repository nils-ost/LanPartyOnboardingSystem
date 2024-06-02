import cherrypy
import cherrypy_cors
from helpers.docdb import docDB
from elements import Session


@cherrypy.popargs('setting_id')
class SettingEndpoint():
    user_readable = ['play_dhcp', 'play_gateway', 'upstream_dns', 'domain', 'subdomain', 'absolute_seatnumbers', 'nlpt_sso', 'sso_login_url']
    admin_writeable = [
        'os_nw_interface', 'play_dhcp', 'play_gateway', 'upstream_dns', 'domain', 'subdomain', 'absolute_seatnumbers',
        'nlpt_sso', 'sso_login_url', 'sso_onboarding_url']
    types_writable = [str, str, str, str, str, str, bool, bool, str, str]

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self, setting_id=None):
        if cherrypy.request.method == 'OPTIONS':
            if setting_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
                cherrypy_cors.preflight(allowed_methods=['GET'])
                return
            else:
                if docDB.get_setting(setting_id) is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {setting_id} not found'}
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, PATCH'
                cherrypy_cors.preflight(allowed_methods=['GET', 'PATCH'])
                return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)

        if cherrypy.request.method == 'GET':
            if setting_id is None:
                admin = len(session.validate_base()) == 0 and session.admin()

                result = list()
                for s in docDB.search_many('settings', {}):
                    if admin or s['_id'] in self.user_readable:
                        result.append({'id': s['_id'], 'value': s['value']})
                cherrypy.response.status = 200
                return result

            else:
                s = docDB.get_setting(setting_id)
                if s is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {setting_id} not found'}

                admin = len(session.validate_base()) == 0 and session.admin()
                if admin or s['_id'] in self.user_readable:
                    cherrypy.response.status = 200
                    return {'id': s['_id'], 'value': s['value']}

                cherrypy.response.status = 403
                return {'error': 'access not allowed'}

        elif cherrypy.request.method == 'PATCH':
            if len(session.validate_base()) != 0 or not session.admin():
                cherrypy.response.status = 403
                return {'error': 'access not allowed'}

            if setting_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
                cherrypy.response.status = 405
                return {'error': 'PATCH not allowed on indexes'}

            else:
                if setting_id not in self.admin_writeable:
                    cherrypy.response.status = 400
                    return {'error': f'setting {setting_id} is not writeable'}
                attr = cherrypy.request.json
                if not isinstance(attr, dict):
                    cherrypy.response.status = 400
                    return {'error': 'submitted data need to be of type dict'}
                if 'value' not in attr:
                    cherrypy.response.status = 400
                    return {'error': 'submitted data needs to contain key named "value"'}
                value_type = self.types_writable[self.admin_writeable.index(setting_id)]
                if not isinstance(attr['value'], value_type):
                    cherrypy.response.status = 400
                    return {'error': f'submitted value needs to be of type {value_type.__name__}'}
                docDB.set_setting(setting_id, attr['value'])
                cherrypy.response.status = 200
                return {'id': setting_id, 'value': attr['value']}

        else:
            if setting_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            else:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, PATCH'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
