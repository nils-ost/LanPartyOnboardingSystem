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
    import docker
    dcli = docker.from_env()

    if ip is None:
        ip = get_client_ip()
    if ip == '127.0.0.1':
        return 'localhost'

    # check dhcp-servers for leases
    if True:
        from elements import VLAN
        for p in [2, 0]:
            for v in VLAN.get_by_purpose(p):
                try:
                    dcon = dcli.containers.get(f'lpos-ipvlan{v["number"]}-dhcp')
                    for line in dcon.exec_run('cat /tmp/kea-leases4.csv').output.decode('utf-8').strip().split('\n'):
                        if ip in line:
                            return line.split(',', 3)[1].replace(':', '')
                except Exception:
                    pass

    # check hosts arp-table, if available (in case this instance is running in a container)
    try:
        dcon = dcli.containers.get('lpos-hostarp')
        for line in dcon.exec_run('cat /proc/net/arp').output.decode('utf-8').strip().split('\n'):
            if str(ip) in line:
                line = line.strip().split()
                if not line[2] == '0x0':
                    return line[3].replace(':', '')
    except Exception:
        pass

    # checking the "own" arp-table
    try:
        r = subprocess.check_output('cat /proc/net/arp | grep ' + str(ip), shell=True).decode('utf-8')
        r = r.strip().split()
        if not r[2] == '0x0':
            return r[3].replace(':', '')
    except Exception:
        pass

    # last resort, just in case a registered Device is not present in any leases-database
    if True:
        from elements import Device, IpPool
        d = Device.get_by_ip(IpPool.dotted_to_int(ip))
        if d is not None:
            return d['mac']

    return 'unknown_device'


def _determine_mgmt_mac_and_ip(return_ip=False, return_mac=False):
    from elements import Setting, Device
    if not return_ip and not return_mac:
        return_ip = True
    if return_ip and return_mac:
        return_mac = False
    mgmt_if = Setting.value('os_nw_interface')
    if mgmt_if == '':
        return None
    for iname, conf in containerd_psutil().items():
        if iname == 'lo' or 'vlan' in iname:
            continue
        if iname == mgmt_if:
            ip, mac = (None, None)
            if 'AF_PACKET' in conf:
                mac = conf['AF_PACKET'].replace(':', '')
            if 'AF_INET' in conf:
                ip = conf['AF_INET'].strip()
            if mac is not None and ip is not None and Device.get_by_mac(mac) is not None:
                Setting.set('lpos_mgmt_mac', mac)
                Setting.set('lpos_mgmt_ip', ip)
                if return_ip:
                    return ip
                else:
                    return mac
    return None


def get_mgmt_mac():
    """
    returns MAC addr of LPOS interface to mgmt network (as string without colons)
    returnvalue can be None, if MAC could not be determined
    """
    from elements import Setting
    mgmt_mac = Setting.value('lpos_mgmt_mac')
    if mgmt_mac is None:
        return _determine_mgmt_mac_and_ip(return_mac=True)
    return mgmt_mac


def get_mgmt_ip():
    """
    returns IP addr of LPOS interface to mgmt network (as string in dotted notation)
    returnvalue can be None, if IP could not be determined
    """
    from elements import Setting
    mgmt_ip = Setting.value('lpos_mgmt_ip')
    if mgmt_ip is None:
        return _determine_mgmt_mac_and_ip(return_ip=True)
    return mgmt_ip


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


def containerd_psutil():
    """
    executes psutil in a container with host-network,
    to be able to retrive interface information from docker host,
    which are in the bridged main container not available
    """
    import json
    import docker
    from prefetcher import docker_images as dima
    dcli = docker.from_env()
    command = list([
        'pip3 install psutil',
        'python3 -c "import psutil, json; print(json.dumps({k: {e.family.name: e.address for e in i} for k, i in psutil.net_if_addrs().items()}))"'
    ])
    dcli.containers.run(network_mode='host', name='lpos-psutil', image=dima['python'], command=f"/bin/sh -c '{';'.join(command)}'")
    dcon = dcli.containers.get('lpos-psutil')
    result = dcon.logs()
    dcon.remove()
    return json.loads(result.decode('utf-8').strip().split('\n')[-1])
