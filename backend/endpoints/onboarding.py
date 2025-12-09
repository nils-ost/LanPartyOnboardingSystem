import cherrypy
import cherrypy_cors
from elements import Device, Table, Seat, Participant, IpPool
from helpers.backgroundworker import device_onboarding_schedule
from helpers.client import get_client_ip, get_client_mac
from elements import Setting


def possible_tables(device):
    from noapiframe import docDB
    result = list()
    if device['port_id'] is None:
        return result
    p = device.port()
    if p['switch_id'] is None:
        return result
    for t in docDB.search_many('Table', {'switch_id': p['switch_id']}):
        result.append(t['number'])
    return result


class OnboardingEndpoint():
    @cherrypy.expose()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST, PUT'
            cherrypy_cors.preflight(allowed_methods=['GET', 'POST', 'PUT'])
            return

        device = Device.get_by_mac(get_client_mac())
        if device is None:
            cherrypy.response.status = 400
            return {'error': {'code': 6, 'desc': 'could not determine device'}}
        if device['ip'] is not None:
            ip = IpPool.octetts_to_int(*[int(o) for o in get_client_ip().split('.')])
            cherrypy.response.status = 201
            if not device['ip'] == ip:
                return {'done': True, 'ip': device['ip'], 'online': False}
            return {'ip': ip, 'online': True}
        if device['onboarding_blocked']:
            cherrypy.response.status = 400
            return {'error': {'code': 7, 'desc': 'device is blocked for onboarding'}}

        if cherrypy.request.method == 'GET':
            cherrypy.response.status = 201
            if Setting.value('nlpt_sso'):
                return {'login_url': Setting.value('sso_login_url')}
            return {'tables': possible_tables(device)}

        elif cherrypy.request.method == 'POST':
            attr = cherrypy.request.json
            absSeatNumbers = Setting.value('absolute_seatnumbers')
            nlpt_sso = Setting.value('nlpt_sso')
            if not isinstance(attr, dict):
                cherrypy.response.status = 400
                return {'error': {'code': 2, 'desc': 'Submitted data need to be of type dict'}}
            if len(attr) == 0:
                cherrypy.response.status = 400
                return {'error': {'code': 3, 'desc': 'data is needed to be submitted'}}
            if nlpt_sso:
                from helpers.sso import nlpt_fetch_participant
                if 'token' not in attr:
                    cherrypy.response.status = 400
                    return {'error': {'code': 4, 'desc': 'token is missing in data'}}
                nlpt_participant = nlpt_fetch_participant(attr['token'])
                if nlpt_participant is None:
                    cherrypy.response.status = 400
                    return {'error': {'code': 15, 'desc': 'could not fetch Participant data from SSO system'}}
                # error-returns for Seat and Device are done further down, if required
                seat = Seat.get_by_number_absolute(int(nlpt_participant['seat']))
                if seat is not None and Device.get_by_seat(seat['_id']) is None:
                    participant = Participant.get_by_login(nlpt_participant['username'])
                    if participant is None:
                        participant = Participant({'login': nlpt_participant['username'], 'name': nlpt_participant['name']})
                    participant.seat(seat)
                    participant.save()
            else:
                if 'pw' not in attr or (not absSeatNumbers and 'table' not in attr) or 'seat' not in attr:
                    cherrypy.response.status = 400
                    return {'error': {'code': 4, 'desc': 'table, seat or pw is missing in data'}}
                elif not isinstance(attr['seat'], int) or (not absSeatNumbers and not isinstance(attr['table'], int)):
                    cherrypy.response.status = 400
                    return {'error': {'code': 5, 'desc': 'table and seat must be of type int'}}
                elif not isinstance(attr['pw'], str):
                    cherrypy.response.status = 400
                    return {'error': {'code': 5, 'desc': 'pw must be of type str'}}
                if not absSeatNumbers and attr['table'] not in possible_tables(device):
                    cherrypy.response.status = 400
                    return {'error': {'code': 8, 'desc': 'invalid table number'}}
                if absSeatNumbers:
                    seat = Seat.get_by_number_absolute(attr['seat'])
                else:
                    table = Table.get_by_number(attr['table'])
                    seat = Seat.get_by_number(table['_id'], attr['seat'])
            if seat is None:
                cherrypy.response.status = 400
                return {'error': {'code': 9, 'desc': 'invalid seat number'}}
            if absSeatNumbers and seat.table()['number'] not in possible_tables(device):
                cherrypy.response.status = 400
                return {'error': {'code': 16, 'desc': 'you are on the wrong table'}}
            if Device.get_by_seat(seat['_id']) is not None:
                cherrypy.response.status = 400
                return {'error': {'code': 10, 'desc': 'seat is allready taken'}}
            if not nlpt_sso and not attr['pw'] == seat['pw']:
                device['pw_strikes'] += 1
                if device['pw_strikes'] >= 3:
                    device['onboarding_blocked'] = True
                device.save()
                cherrypy.response.status = 400
                return {'error': {'code': 11, 'desc': 'wrong password'}}
            participant = Participant.get_by_seat(seat['_id'])
            if participant is None:
                cherrypy.response.status = 400
                return {'error': {'code': 12, 'desc': 'Seat is not associated to a Participant'}}
            seat['claiming_device_id'] = device['_id']
            seat.save()
            cherrypy.response.status = 201
            return {'participant': participant['name']}

        elif cherrypy.request.method == 'PUT':
            attr = cherrypy.request.json
            if not isinstance(attr, dict):
                cherrypy.response.status = 400
                return {'error': {'code': 2, 'desc': 'Submitted data need to be of type dict'}}
            elif len(attr) == 0:
                cherrypy.response.status = 400
                return {'error': {'code': 3, 'desc': 'data is needed to be submitted'}}
            elif 'choice' not in attr:
                cherrypy.response.status = 400
                return {'error': {'code': 4, 'desc': 'choice is missing in data'}}
            elif not isinstance(attr['choice'], bool):
                cherrypy.response.status = 400
                return {'error': {'code': 5, 'desc': 'choice must be of type bool'}}
            seat = Seat.get_by_claiming(device['_id'])
            if seat is None:
                cherrypy.response.status = 400
                return {'error': {'code': 13, 'desc': 'missing steps'}}
            if not attr['choice']:
                seat['claiming_device_id'] = None
                seat.save()
                device['onboarding_blocked'] = True
                device.save()
                cherrypy.response.status = 400
                return {'error': {'code': 14, 'desc': 'contact admin'}}
            device['seat_id'] = seat['_id']
            device.save()
            seat['claiming_device_id'] = None
            seat.save()
            # configure and reset Switch-Port
            device_onboarding_schedule(device['_id'])
            cherrypy.response.status = 201
            return {'done': True, 'ip': device['ip']}

        else:
            cherrypy.response.headers['Allow'] = 'OPTIONS, GET, POST, PUT'
            cherrypy.response.status = 405
            return {'error': {'code': 1, 'desc': 'method not allowed'}}
