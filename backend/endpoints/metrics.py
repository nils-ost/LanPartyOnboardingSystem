from helpers.config import get_config
from multiprocessing import Process

metrics_exporter_process = None


def start_metrics_exporter():
    global metrics_exporter_process

    def metrics_exporter_function():
        import cherrypy
        from elements import Participant, Device, Seat, Table

        class Metrics():
            @cherrypy.expose()
            def index(self):
                lines = list()

                # Participants Count
                lines.append('# HELP lpos_participants_count Current number of Participants existing on LPOS')
                lines.append('# TYPE lpos_participants_count gauge')
                lines.append(f'lpos_participants_count{{}} {Participant.count()}')

                # Participants Seated Count(Participants where seat_id != None)
                lines.append('# HELP lpos_participants_seated Current number of Participants with assigned Seat')
                lines.append('# TYPE lpos_participants_seated gauge')
                filter = {'seat_id': {'$ne': None}}
                lines.append(f'lpos_participants_seated{{}} {Participant.count(filter)}')

                # Participants Onboarded Count(Devices where seat_id != None and participant_id != None)
                lines.append('# HELP lpos_participants_onboarded Current number of Participants where onboarding is completed')
                lines.append('# TYPE lpos_participants_onboarded gauge')
                filter = {'seat_id': {'$ne': None}, 'participant_id': {'$ne': None}}
                lines.append(f'lpos_participants_onboarded{{}} {Device.count(filter)}')

                # Participants Extra Devices Count(Devices where seat_id == None and participant_id != None)
                lines.append('# HELP lpos_participants_extra_devices Current number of Devices that are onboarded but arent the primary Device of Participants')
                lines.append('# TYPE lpos_participants_extra_devices gauge')
                filter = {'seat_id': None, 'participant_id': {'$ne': None}}
                lines.append(f'lpos_participants_extra_devices{{}} {Device.count(filter)}')

                # Devices Count
                lines.append('# HELP lpos_devices_count Current number of Devices existing on LPOS')
                lines.append('# TYPE lpos_devices_count gauge')
                lines.append(f'lpos_devices_count{{}} {Device.count()}')

                # Devices Managed Count(Devices where ip != None)
                lines.append('# HELP lpos_devices_managed Current number of Devices with assigned IP in LPOS')
                lines.append('# TYPE lpos_devices_managed gauge')
                filter = {'ip': {'$ne': None}}
                lines.append(f'lpos_devices_managed{{}} {Device.count(filter)}')

                # Seats Count
                lines.append('# HELP lpos_seats_count Current number of Seats existing on LPOS')
                lines.append('# TYPE lpos_seats_count gauge')
                lines.append(f'lpos_seats_count{{}} {Seat.count()}')

                # Tables Count
                lines.append('# HELP lpos_tables_count Current number of Tables existing on LPOS')
                lines.append('# TYPE lpos_tables_count gauge')
                lines.append(f'lpos_tables_count{{}} {Table.count()}')

                # Seates on Table (per Table)
                lines.append('# HELP lpos_table_seats Number of Seats per to Table')
                lines.append('# TYPE lpos_table_seats gauge')
                for table in Table.all():
                    filter = {'table_id': table['_id']}
                    lines.append(f'lpos_table_seats{{number="{table["number"]}",desc="{table["desc"]}"}} {Seat.count(filter)}')

                # Onboarded Seats on Table (per Table)
                lines.append('# HELP lpos_table_seats_onboarded Number of Seats, that are onboarded, per to Table')
                lines.append('# TYPE lpos_table_seats_onboarded gauge')
                onboarded_seat_ids = list()
                for device in Device.all():
                    if device['seat_id'] is not None and device['participant_id'] is not None:
                        onboarded_seat_ids.append(device['seat_id'])
                for table in Table.all():
                    count = 0
                    for seat in Seat.get_by_table(table['_id']):
                        if seat['_id'] in onboarded_seat_ids:
                            count += 1
                    lines.append(f'lpos_table_seats_onboarded{{number="{table["number"]}",desc="{table["desc"]}"}} {count}')

                cherrypy.response.headers['Cache-Control'] = 'no-cache'
                cherrypy.response.headers['Content-Type'] = 'text/plain; version=0.0.4'
                return '\n'.join(lines)

        config = get_config('metrics')
        cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': config['port']})
        cherrypy.quickstart(Metrics(), '/metrics')

    config = get_config('metrics')
    if config['enabled'] and metrics_exporter_process is None:
        metrics_exporter_process = Process(target=metrics_exporter_function, daemon=True)
        metrics_exporter_process.start()
