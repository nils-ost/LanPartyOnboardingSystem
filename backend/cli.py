import os
import sys
import argparse
import json
import time
import subprocess
from datetime import datetime
os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser(description='LPOS CLI')
parser.add_argument('--config', dest='config', action='store_true', default=False, help='Returns current configuration')
parser.add_argument('--enablemetrics', dest='enablemetrics', action='store_true', default=False, help='If set the LPOS metrics endpoint is set to enabled')
parser.add_argument('--state', '-s', dest='state', action='store_true', default=False, help='If set the state of LPOS stack is displayed')
parser.add_argument('--start', dest='start', action='store_true', default=False, help='If set LPOS stack is started')
parser.add_argument('--stop', dest='stop', action='store_true', default=False, help='If set LPOS stack is stopped')
parser.add_argument('--restart', dest='restart', action='store_true', default=False, help='If set LPOS stack is restarted')
parser.add_argument('--version', dest='version', action='store_true', default=False, help='Displays the Version of DB and LPOS')
args = parser.parse_args()


class bcolors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def version():
    from helpers.docdb import docDB
    return docDB.get_setting('version')


def state():
    print(f'Version of DB and LPOS: {bcolors.GREEN}v{version()}{bcolors.ENDC}')
    # lpos.service
    active = subprocess.call('systemctl is-active lpos.service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
    print(f"{' ' * 10}lpos.service: {bcolors.GREEN + 'active' if active else bcolors.FAIL + 'inactive'}{bcolors.ENDC}")
    # docker.mongodb.service
    for service in ['docker.mongodb.service']:
        present = subprocess.call(f'systemctl cat {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
        if present:
            active = subprocess.call(f'systemctl is-active {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
        if service == 'docker.mongodb.service':
            from helpers.docdb import docDB
            connected = docDB.is_connected()

        state = 'locally ' if present else 'remotely '
        if present:
            state += (bcolors.GREEN + 'active ' if active else bcolors.FAIL + 'inactive ') + bcolors.ENDC
        state += (bcolors.GREEN + 'connectable' if connected else bcolors.FAIL + 'unconnectable') + bcolors.ENDC
        print(f'{" " * (22 - len(service))}{service}: {state}')
    # docker.haproxy.service
    if subprocess.call('systemctl cat docker.haproxy.service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
        active = subprocess.call('systemctl is-active docker.haproxy.service', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
        state = (bcolors.GREEN + 'active' if active else bcolors.FAIL + 'inactive') + bcolors.ENDC
    else:
        state = bcolors.WARNING + 'not present' + bcolors.ENDC
    print(f'docker.haproxy.service: {state}')


def stop_stack():
    for service in ['lpos.service', 'docker.haproxy.service', 'docker.mongodb.service']:
        if subprocess.call(f'systemctl cat {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
            if subprocess.call(f'systemctl is-active {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
                subprocess.call(f'systemctl stop {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                print(f'Stopped {service}')


def start_stack():
    for service in ['docker.mongodb.service', 'lpos.service', 'docker.haproxy.service']:
        if subprocess.call(f'systemctl cat {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
            if not subprocess.call(f'systemctl is-active {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
                subprocess.call(f'systemctl start {service}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                print(f'Started {service}')


def restart_stack():
    stop_stack()
    time.sleep(1)
    start_stack()


def create_admin():
    from elements import Participant
    user = input('Username: ').strip()
    p = Participant.get_by_login(user)
    if p is not None:
        print('Participant with this name allready exists!')
        return
    p = Participant()
    p['login'] = user
    p['pw'] = input('Password: ').strip()
    p['admin'] = True
    p.save()


def set_os_nw_interface():
    from helpers.docdb import docDB
    iname = input('Enter name of network interface to be used for VLANs on this machine: ').strip()
    docDB.set_setting('os_nw_interface', iname)


def set_domain():
    from helpers.docdb import docDB
    domain = input('Enter domain of local network: ').strip().strip('.')
    docDB.set_setting('domain', domain)


def set_subdomain():
    from helpers.docdb import docDB
    subdomain = input('Enter subdomain name of LPOS (without domain of local network): ').strip().strip('.')
    docDB.set_setting('subdomain', subdomain)


def set_dhcpip():
    from helpers.docdb import docDB
    gateway = input('Enter IP the DHCP-Server should get in the play-network: ').strip().strip('.')
    docDB.set_setting('play_dhcp', gateway)


def set_gateway():
    from helpers.docdb import docDB
    gateway = input('Enter IP of gateway to the internet for the play-network: ').strip().strip('.')
    docDB.set_setting('play_gateway', gateway)


def set_upstream():
    from helpers.docdb import docDB
    upstream = input('Enter IP of upstream DNS-Server: ').strip().strip('.')
    docDB.set_setting('upstream_dns', upstream)


def clearDB(force=False):
    if not force and not input('Wipe all data on database? (y/N): ').strip() == 'y':
        return
    from helpers.docdb import docDB
    docDB.clear()


def createBackup():
    from helpers.docdb import docDB
    from helpers.config import get_config
    from helpers.version import version
    import zipfile
    path = input('Where do you like to store the backup?: ')
    if not os.path.isdir(path):
        print(f'{path} is not a valid directory!')
        return
    dt = datetime.now()
    backup_file = os.path.join(path, 'lpos_backup_' + dt.strftime('%Y%m%d%M%H%S') + '.zip')

    metadata = dict({
        'ts': int(dt.timestamp()),
        'version': version,
        'db': dict()
    })

    with zipfile.ZipFile(backup_file, mode='w') as zf:
        with zf.open('config.json', 'w') as f:
            f.write(json.dumps(get_config(), indent=2).encode('utf-8'))

        for coll in [c['name'] for c in docDB.conn().list_collections()]:
            elements = list()
            for element in docDB.conn().get_collection(coll).find({}):
                elements.append(element)
            with zf.open(f'db/{coll}.json', 'w') as f:
                f.write(json.dumps(elements, indent=2).encode('utf-8'))
            metadata['db'][coll] = len(elements)

        with zf.open('metadata.json', 'w') as f:
            f.write(json.dumps(metadata, indent=2).encode('utf-8'))
    print(f'Backup written to: {backup_file}')


def restoreBackup():
    import zipfile
    from helpers.version import version
    from helpers.versioning import versions_gt
    from helpers.config import reload_config
    from helpers.docdb import docDB
    backup_file = input('Path to backup-file: ').strip()
    if not os.path.isfile(backup_file):
        print('Invalid file-backup_file!')
        return

    metadata = dict({
        'version': '0',
        'db': dict()
    })

    with zipfile.ZipFile(backup_file, mode='r') as zf:
        with zf.open('metadata.json', 'r') as f:
            metadata.update(json.load(f))
        if versions_gt(metadata['version'], version):
            print(f"Version of backup ({metadata['version']}) is bigger than the currently installed version ({version})! Can't restore backup!")
            return

        clearDB(force=True)
        with zf.open('config.json', 'r') as f:
            with open('config.json', 'wb') as out:
                out.write(f.read())
        reload_config()
        docDB.reset_connections()
        clearDB(force=True)

        for coll in metadata.get('db', dict()).keys():
            with zf.open(f'db/{coll}.json') as f:
                for element in json.load(f):
                    docDB.conn().get_collection(coll).insert_one(element)

    print(f'Restored backup: {backup_file}')


def exit():
    sys.exit(0)


commands = [
    ('Stack State', state),
    ('Start Stack', start_stack),
    ('Stop Stack', stop_stack),
    ('Restart Stack', restart_stack),
    ('Create Admin', create_admin),
    ('Set OS Network Interface for VLANs', set_os_nw_interface),
    ('Set local network domain', set_domain),
    ('Set LPOS subdomain', set_subdomain),
    ('Set play dhcp IP', set_dhcpip),
    ('Set play gateway IP', set_gateway),
    ('Set upstream DNS IP', set_upstream),
    ('Clear DB', clearDB),
    ('Create Backup', createBackup),
    ('Restore Backup', restoreBackup),
    ('Exit', exit)
]

if args.config:
    from helpers.config import get_config
    print(json.dumps(get_config(), indent=2))
    sys.exit(0)

if args.enablemetrics:
    from helpers.config import get_config, set_config
    config = get_config('metrics')
    if not config.get('enabled', False):
        config['enabled'] = True
        set_config(config, 'metrics')
    sys.exit(0)

if args.state:
    state()
    sys.exit(0)

if args.start:
    start_stack()
    sys.exit(0)

if args.stop:
    stop_stack()
    sys.exit(0)

if args.restart:
    restart_stack()
    sys.exit(0)

if args.version:
    print(version())
    sys.exit(0)

while True:
    index = 0
    for display, func in commands:
        print(f'{index} {display}')
        index += 1

    selection = int(input('\nSelect: '))
    if selection not in range(0, len(commands)):
        print('Invalid input!')
        sys.exit(1)

    commands[selection][1]()
    print()
