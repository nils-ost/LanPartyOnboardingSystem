import cherrypy
import cherrypy_cors
from noapiframe import ElementEndpointBase
from elements import Participant, Session


class ParticipantEndpoint(ElementEndpointBase):
    _element = Participant
    _session_cls = Session

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def offboard(self, element_id=None):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, PUT'
            cherrypy_cors.preflight(allowed_methods=['PUT'])
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

        if cherrypy.request.method == 'PUT':
            if element_id is None:
                cherrypy.response.status = 404
                return {'error': 'need a Participant ID for a Participant to be commited'}

            p = Participant.get(element_id)
            if p['_id'] is None:
                cherrypy.response.status = 404
                return {'error': f'id {element_id} not found'}

            try:
                p.offboard()
            except Exception:
                cherrypy.response.status = 400
                return {'error': 'offboarding did not work'}

            if p['seat_id'] is None:
                cherrypy.response.status = 201
                return {'desc': 'offboarded'}
            else:
                cherrypy.response.status = 400
                return {'error': 'offboarding did not work'}
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, PUT'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
