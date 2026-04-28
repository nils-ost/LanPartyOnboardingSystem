import cherrypy
import subprocess
import logging

logger = logging.getLogger(__name__)


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
        import docker
        from elements import VLAN
        dcli = docker.from_env()
        for p in [2, 0]:
            for v in VLAN.get_by_purpose(p):
                try:
                    dcon = dcli.containers.list(filters={'name': f'lpos-ipvlan{v["number"]}-dhcp'})[0]
                    r = dcon.exec_run(f'cat /tmp/kea-leases4.csv | grep {ip}')
                    if r.exit_code == 0:
                        return r.output.decode('utf-8').strip().split('\n')[-1].split(',', 3)[1].replace(':', '')
                except Exception:
                    pass

    if True:  # last resort, just in case a registered Device is not present in any leases-database
        from elements import Device, IpPool
        d = Device.get_by_ip(IpPool.dotted_to_int(ip))
        if d is not None:
            return d['mac']

    return 'unknown_device'


def nslookup(domain):
    from helpers.haproxy import lposHAproxy
    logger.info(f'executing nslookup of {domain}')
    try:
        addr = False
        for line in lposHAproxy.execute_command(f'nslookup -type=a {domain}').strip().split('\n'):
            if line.startswith('Name') and line.split(':')[-1].strip() == domain:
                addr = True
            if line.startswith('Address') and addr:
                return line.split(':')[-1].strip()
        else:
            logger.warning('address could not be determined')
            return None
    except Exception:
        logger.warning("haproxy container not started or can't be found")
