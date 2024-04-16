import cherrypy
import subprocess


def get_client_ip():
    if 'X-Forwarded-For' in cherrypy.request.headers:  # needs to be used in case haproxy is used in front of LPOS
        return cherrypy.request.headers['X-Forwarded-For']
    else:
        return cherrypy.request.remote.ip


def get_client_mac(ip=None):
    if ip is None:
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

    if True:
        from elements import VLAN
        dcmd = 'docker' if int(subprocess.check_output('id -u', shell=True).decode('utf-8').strip()) == 0 else 'sudo docker'
        for p in [2, 0]:
            for v in VLAN.get_by_purpose(p):
                try:
                    r = subprocess.check_output(f'{dcmd} exec lpos-ipvlan{v["number"]}-dhcp cat /tmp/kea-leases4.csv | grep {ip}', shell=True)
                    return r.decode('utf-8').strip().split('\n')[-1].split(',', 3)[1].replace(':', '')
                except Exception:
                    pass

    if True:  # last resort, just in case a registered Device is not present in any leases-database
        from elements import Device, IpPool
        d = Device.get_by_ip(IpPool.dotted_to_int(ip))
        if d is not None:
            return d['mac']

    return 'unknown_device'
