import cherrypy
import cherrypy_cors
from noapiframe import ElementEndpointBase
from elements import Session, Switch


class SwitchEndpoint(ElementEndpointBase):
    _element = Switch
    _session_cls = Session
    _ro_attr = ['commited']

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit(self, element_id=None):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get(self._session_cls.cookie_name)
        if cookie:
            session = self._session_cls.get(cookie.value)
        else:
            session = self._session_cls.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            if element_id is None:
                cherrypy.response.status = 404
                return {'error': 'need a Switch ID for a Switch to be commited'}

            s = Switch.get(element_id)
            if s['_id'] is None:
                cherrypy.response.status = 404
                return {'error': f'id {element_id} not found'}

            try:
                s.commit()
            except Exception:
                cherrypy.response.status = 400
                return {'error': 'commit did not work'}

            if s['commited']:
                cherrypy.response.status = 201
                return {'desc': 'commited'}
            else:
                cherrypy.response.status = 400
                return {'error': 'commit did not work'}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def retreat(self, element_id=None):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy_cors.preflight(allowed_methods=['POST'])
            return

        cookie = cherrypy.request.cookie.get(self._session_cls.cookie_name)
        if cookie:
            session = self._session_cls.get(cookie.value)
        else:
            session = self._session_cls.get(None)
        if len(session.validate_base()) > 0:
            cherrypy.response.status = 401
            return {'error': 'not authorized'}
        elif not session.admin():
            cherrypy.response.status = 403
            return {'error': 'access not allowed'}

        if cherrypy.request.method == 'POST':
            if element_id is None:
                cherrypy.response.status = 404
                return {'error': 'need a Swith ID for a Switch to be retreated'}

            s = Switch.get(element_id)
            if s['_id'] is None:
                cherrypy.response.status = 404
                return {'error': f'id {element_id} not found'}

            try:
                s.retreat()
            except Exception:
                return {'error': 'retreat did not work'}

            if not s['commited']:
                cherrypy.response.status = 201
                return {'desc': 'retreated'}
            else:
                cherrypy.response.status = 400
                return {'error': 'retreat did not work'}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
