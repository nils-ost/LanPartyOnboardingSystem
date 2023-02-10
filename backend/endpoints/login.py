import cherrypy
import cherrypy_cors
from datetime import datetime
from elements import Session, Participant


class LoginEndpoint():
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self, user=None):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])
            return
        elif cherrypy.request.method == 'GET':
            if user is not None:
                p = Participant.get_by_login(user)
                if p is not None:
                    s = Session({'participant_id': p['_id'], 'complete': False, 'ip': cherrypy.request.remote.ip})
                    s['till'] = int(datetime.now().timestamp() + 300)
                    cherrypy.session['session_id'] = s.save().get('created')
                    return {'session_id': s['_id'], 'complete': s['complete']}
                else:
                    return {'error': 'user does not exist'}
            else:
                s = Session.get(cherrypy.session.get('session_id'))
                if len(s.validate_base()) == 0:
                    return {'session_id': s['_id'], 'complete': s['complete']}
                else:
                    return {'error': 'invalid session'}
        """
        elif cherrypy.request.method == 'POST':
            attr = cherrypy.request.json
            if not isinstance(attr, dict):
                cherrypy.response.status = 400
                return {'error': 'Submitted data need to be of type dict'}
            elif len(attr) == 0:
                cherrypy.response.status = 400
                return {'error': 'data is needed to be submitted'}
            attr.pop('_id', None)
            el = self._element(attr)
            result = el.save()
            if 'errors' in result:
                cherrypy.response.status = 400
            else:
                cherrypy.response.status = 201
            return result
        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST'
            cherrypy.response.status = 405
            return {'error': 'method not allowed'}
        """
