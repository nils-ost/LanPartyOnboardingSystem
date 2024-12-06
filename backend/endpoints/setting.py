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

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self, element_id=None):
        if cherrypy.request.method == 'OPTIONS':
            if element_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, DELETE'
                cherrypy_cors.preflight(allowed_methods=['GET', 'DELETE'])
                return
            else:
                el = self._element.get(element_id)
                if el['_id'] is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, PATCH, DELETE'
                cherrypy_cors.preflight(allowed_methods=['GET', 'PATCH', 'DELETE'])
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
                    return el.json()
                else:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
            else:
                result = list()
                for el in self._element.all():
                    if admin or el['_id'] in self.user_readable:
                        result.append(el.json())
                return result
        elif cherrypy.request.method == 'PATCH':
            if self._restrict_write and not admin:
                cherrypy.response.status = 403
                return {'error': 'access not allowed'}
            if element_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
                cherrypy.response.status = 405
                return {'error': 'PATCH not allowed on indexes'}
            else:
                el = self._element.get(element_id)
                if el['_id'] is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
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
        elif cherrypy.request.method == 'DELETE':
            if self._restrict_write and not admin:
                cherrypy.response.status = 403
                return {'error': 'access not allowed'}
            if element_id is None:
                deleted_ids = list()
                for el in self._element.all():
                    r = el.delete()
                    if 'delete' in r:
                        deleted_ids.append(r['delete'])
                return {'deleted': deleted_ids}
            else:
                el = self._element.get(element_id)
                if el['_id'] is None:
                    cherrypy.response.status = 404
                    return {'error': f'id {element_id} not found'}
                result = el.delete()
                if 'deleted' not in result:
                    cherrypy.response.status = 400
                return result
        else:
            if element_id is None:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, DELETE'
            else:
                cherrypy.response.headers['Allow'] = 'OPTIONS, GET, PATCH, DELETE'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
