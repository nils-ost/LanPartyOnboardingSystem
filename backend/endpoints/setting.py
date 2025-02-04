import cherrypy
import cherrypy_cors
from elements import Session, Setting


@cherrypy.popargs('element_id')
class SettingEndpoint():
    _element = Setting
    _restrict_read = False  # if set to True only admin Participants are allowed to use reading methods
    _restrict_write = True  # if set to True only admin Participants are allowed to use writing methods
    _ro_attr = list()  # List of attribute-names, that are allways read-only
    user_readable = ['domain', 'subdomain', 'absolute_seatnumbers', 'nlpt_sso', 'sso_login_url']
    admin_writeable = ['os_nw_interface', 'play_dhcp', 'play_gateway', 'upstream_dns', 'domain', 'subdomain', 'absolute_seatnumbers', 'nlpt_sso',
                       'sso_login_url', 'sso_onboarding_url', 'server_port', 'metrics_enabled', 'metrics_port',
                       'haproxy_api_host', 'haproxy_api_port', 'haproxy_api_user', 'haproxy_api_pw']

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self, element_id=None):
        if cherrypy.request.method == 'OPTIONS':
            if element_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
                cherrypy_cors.preflight(allowed_methods=['GET'])
                return
            else:
                el = self._element.get(element_id)
                if el['_id'] is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, PATCH'
                cherrypy_cors.preflight(allowed_methods=['GET', 'PATCH'])
                return

        cookie = cherrypy.request.cookie.get('LPOSsession')
        if cookie:
            session = Session.get(cookie.value)
        else:
            session = Session.get(None)
        admin = len(session.validate_base()) == 0 and session.admin()

        if cherrypy.request.method == 'GET':
            if self._restrict_read and not admin:
                cherrypy.response.status = 403
                return {'error': 'access not allowed'}
            if element_id is not None:
                el = self._element.get(element_id)
                if el['_id'] is not None and (admin or el['_id'] in self.user_readable):
                    result = el.json()
                    result['ro'] = True if not admin or element_id not in self.admin_writeable else False
                    return result
                else:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
            else:
                result = list()
                for el in self._element.all():
                    if admin or el['_id'] in self.user_readable:
                        r = el.json()
                        r['ro'] = True if not admin or el['_id'] not in self.admin_writeable else False
                        result.append(r)
                return result
        elif cherrypy.request.method == 'PATCH':
            if self._restrict_write and not admin:
                cherrypy.response.status = 403
                return {'error': 'access not allowed'}
            if element_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
                cherrypy.response.status = 405
                return {'error': 'PATCH not allowed on indexes'}
            else:
                el = self._element.get(element_id)
                if el['_id'] is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
                if element_id not in self.admin_writeable:
                    cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
                    cherrypy.response.status = 405
                    return {'error': f'{element_id} is read-only'}
                attr = cherrypy.request.json
                if not isinstance(attr, dict):
                    cherrypy.response.status = 400
                    return {'error': 'Submitted data need to be of type dict'}
                attr.pop('_id', None)
                for k, v in attr.items():
                    if k not in self._ro_attr:
                        el[k] = v
                result = el.save()
                if 'errors' in result:
                    cherrypy.response.status = 400
                else:
                    cherrypy.response.status = 201
                return result
        else:
            if element_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            else:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, PATCH'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
