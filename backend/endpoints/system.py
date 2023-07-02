import cherrypy
import cherrypy_cors
from elements import Session


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
            result['commited'] = False
            result['open_commits'] = True
            return result
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}

    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def commit(self):
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
    def retreat(self):
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
