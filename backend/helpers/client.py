import cherrypy
import subprocess


def get_client_ip():
    if 'X-Forwarded-For' in cherrypy.request.headers:  # needs to be used in case haproxy is used in front of LPOS
        return cherrypy.request.headers['X-Forwarded-For']
    else:
        return cherrypy.request.remote.ip


def get_client_mac():
    # TODO: rework for kea dhcp
    ip = get_client_ip()
    if ip == '127.0.0.1':
        return 'localhost'
    try:
        r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True).decode('utf-8')
        r = r.strip().split()
        if not r[2] == '0x0':
            return r[3].replace(':', '')
    except Exception:
        pass
    try:
        r = subprocess.check_output('cat /var/lib/misc/dnsmasq.leases | grep ' + str(ip), shell=True).decode('utf-8')
        return r.strip().split()[1].replace(':', '')
    except Exception:
        return 'unknown_mac'
