from helpers.config import get_config
from multiprocessing import Process

metrics_exporter_process = None


def start_metrics_exporter():
    global metrics_exporter_process

    def metrics_exporter_function():
        import cherrypy
        from elements import Switch

        class Metrics():
            @cherrypy.expose()
            def index(self):
                swi = dict()
                for s in Switch.all():
                    swi[s['addr']] = dict({'desc': s['desc'], 'metrics': s.metrics()})
                lines = list()
                lines.append('# HELP swi_rx_bytes_total Total number of Bytes received on a switch-port')
                lines.append('# TYPE swi_rx_bytes_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['rb'])):
                        lines.append(f'swi_rx_bytes_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["rb"][idx]}')

                lines.append('# HELP swi_tx_bytes_total Total number of Bytes transmitted on a switch-port')
                lines.append('# TYPE swi_tx_bytes_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['tb'])):
                        lines.append(f'swi_tx_bytes_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["tb"][idx]}')

                lines.append('# HELP swi_rx_packets_total Total number of Packets received on a switch-port')
                lines.append('# TYPE swi_rx_packets_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['rtp'])):
                        lines.append(f'swi_rx_packets_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["rtp"][idx]}')

                lines.append('# HELP swi_tx_packets_total Total number of Packets transmitted on a switch-port')
                lines.append('# TYPE swi_tx_packets_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['ttp'])):
                        lines.append(f'swi_tx_packets_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["ttp"][idx]}')

                lines.append('# HELP swi_rx_broadcasts_total Total number of Broadcasts received on a switch-port')
                lines.append('# TYPE swi_rx_broadcasts_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['rbp'])):
                        lines.append(f'swi_rx_broadcasts_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["rbp"][idx]}')

                lines.append('# HELP swi_tx_broadcasts_total Total number of Broadcasts transmitted on a switch-port')
                lines.append('# TYPE swi_tx_broadcasts_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['tbp'])):
                        lines.append(f'swi_tx_broadcasts_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["tbp"][idx]}')

                lines.append('# HELP swi_rx_unicasts_total Total number of Unicasts received on a switch-port')
                lines.append('# TYPE swi_rx_unicasts_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['rup'])):
                        lines.append(f'swi_rx_unicasts_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["rup"][idx]}')

                lines.append('# HELP swi_tx_unicasts_total Total number of Unicasts transmitted on a switch-port')
                lines.append('# TYPE swi_tx_unicasts_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['tup'])):
                        lines.append(f'swi_tx_unicasts_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["tup"][idx]}')

                lines.append('# HELP swi_rx_multicasts_total Total number of Multicasts received on a switch-port')
                lines.append('# TYPE swi_rx_multicasts_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['rmp'])):
                        lines.append(f'swi_rx_multicasts_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["rmp"][idx]}')

                lines.append('# HELP swi_tx_multicasts_total Total number of Multicasts transmitted on a switch-port')
                lines.append('# TYPE swi_tx_multicasts_total counter')
                for addr, s in swi.items():
                    for idx in range(len(s['metrics']['tmp'])):
                        lines.append(f'swi_tx_multicasts_total{{swi_addr="{addr}",swi_desc="{s["desc"]}",port="{idx + 1}"}} {s["metrics"]["tmp"][idx]}')

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
