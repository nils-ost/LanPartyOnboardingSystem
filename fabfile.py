from fabric import task
import patchwork.transfers
import os
import json
import time
from datetime import datetime

apt_update_run = False
project_dir = '/opt/middleware/lpos'
backup_dir = '/var/backup'
storagedir_mongo = '/var/data/mongodb'
mongodb_image = 'mongo:4.4'
mongodb_service = 'docker.mongodb.service'
mongoexporter_image = 'bitnami/mongodb-exporter:0.30.0'
mongoexporter_service = 'docker.mongoexporter.service'
haproxy_image = 'haproxytech/haproxy-alpine:latest'
haproxy_service = 'docker.haproxy.service'
haproxy_config = '/etc/haproxy/haproxy.cfg'
lpos_service = 'lpos.service'
dns_image = 'coredns/coredns:1.11.1'
dhcp_image = 'docker.cloudsmith.io/isc/docker/kea-dhcp4:2.5.7'
alpine_image = 'alpine'


def docker_pull(c, image):
    print(f'Preloading docker image {image}')
    c.run(f'docker pull {image}')


def docker_prune(c):
    print('Removing all outdated docker images')
    c.run('docker image prune -f')


def systemctl_stop(c, service):
    if c.run(f'systemctl is-active {service}', warn=True, hide=True).ok:
        print(f'Stop Service {service}', flush=True)
        c.run(f'systemctl stop {service}', hide=True)


def systemctl_start(c, service):
    if not c.run(f'systemctl is-enabled {service}', warn=True, hide=True).ok:
        print(f'Enable Service {service}', flush=True)
        c.run(f'systemctl enable {service}', hide=True)
    if c.run(f'systemctl is-active {service}', warn=True, hide=True).ok:
        print(f'Restart Service {service}', flush=True)
        c.run(f'systemctl restart {service}', hide=True)
    else:
        print(f'Start Service {service}', flush=True)
        c.run(f'systemctl start {service}', hide=True)


def systemctl_start_docker(c):
    if not c.run('systemctl is-enabled docker', warn=True, hide=True).ok:
        print('Enable Service docker', flush=True)
        c.run('systemctl enable docker', hide=True)
    if c.run('systemctl is-active docker', warn=True, hide=True).ok:
        print('Service docker allready running', flush=True)
    else:
        print('Start Service docker', flush=True)
        c.run('systemctl start docker', hide=True)


def systemctl_install_service(c, local_file, remote_file, replace_macros):
    print(f'Installing Service {remote_file}', flush=True)
    c.put(os.path.join('install', local_file), remote=os.path.join('/etc/systemd/system', remote_file))
    for macro, value in replace_macros:
        c.run("sed -i -e 's/" + macro + '/' + value.replace('/', r'\/') + "/g' " + os.path.join('/etc/systemd/system', remote_file))


def install_rsyslog(c):
    print('Configuring rsyslog for LPOS')
    c.put('install/rsyslog.conf', '/etc/rsyslog.d/lpos.conf')
    systemctl_start(c, 'rsyslog')


def install_logrotate(c):
    print('Configuring logrotate for LPOS')
    c.put('install/logrotate', '/etc/logrotate.d/lpos')
    c.run('chmod 644 /etc/logrotate.d/lpos')


def setup_virtualenv(c, pdir):
    print(f'Setup virtualenv for {pdir}')
    c.run(f"virtualenv -p /usr/bin/python3 {os.path.join(pdir, 'venv')}")
    print(f'Installing python requirements for {pdir}')
    c.run(f"{os.path.join(pdir, 'venv/bin/pip')} install -r {os.path.join(pdir, 'requirements.txt')}")


def upload_project_files(c):
    for f in ['main.py', 'cli.py', 'requirements.txt']:
        print(f'Uploading {f}')
        c.put(os.path.join('backend', f), remote=os.path.join(project_dir, f))
    for d in ['backend/elements', 'backend/endpoints', 'backend/helpers', 'backend/MTSwitch']:
        print(f'Uploading {d}')
        patchwork.transfers.rsync(c, d, project_dir, exclude=['*.pyc', '*__pycache__'], delete=True)
    for d in ['backend/static/ang']:
        print(f'Uploading {d}')
        patchwork.transfers.rsync(c, d, os.path.join(project_dir, 'static'), exclude=['*.pyc', '*__pycache__'], delete=True)


def prepare_lpos_cli(c):
    c.run(f"echo -e '#!/bin/bash\n{os.path.join(project_dir, 'venv/bin/python')} {os.path.join(project_dir, 'cli.py')} $*' > /usr/bin/lpos")
    c.run('chmod 755 /usr/bin/lpos')


def create_directorys_mongodb(c):
    for d in [storagedir_mongo, backup_dir]:
        print(f'Creating {d}')
        c.run(f'mkdir -p {d}', warn=True, hide=True)


def create_directorys_lpos(c):
    for d in [project_dir]:
        print(f'Creating {d}')
        c.run(f'mkdir -p {d}', warn=True, hide=True)


def install_apt_package(c, package):
    global apt_update_run
    if not c.run(f'dpkg -s {package}', warn=True, hide=True).ok:
        if not apt_update_run:
            print('Running apt update')
            c.run('apt update', hide=True)
            apt_update_run = True
        print(f'Installing {package}')
        c.run(f'apt install -y {package}')
    else:
        print(f'{package} allready installed')


def install_docker(c):
    if not c.run('which docker', warn=True, hide=True).ok:
        print('Install Docker')
        c.run('curl -fsSL https://get.docker.com | sh')
    else:
        print('Docker allready installed')


def backup_mongodb(c):
    if c.run(f'systemctl is-active {mongodb_service}', warn=True, hide=True).ok:
        backup_path = os.path.join(backup_dir, 'mongodb-' + datetime.now().isoformat() + '.tar.gz')
        print(f'Creating backup: {backup_path}', flush=True)
        c.run(f'docker exec -t {mongodb_service} /bin/sh -c "mongodump --forceTableScan -o /backup; tar cfz /backup.tar.gz /backup; rm -rf /backup"', hide=True)
        c.run(f'docker cp {mongodb_service}:/backup.tar.gz {backup_path}', hide=True)


def reassign_docker_iptables_rules(c):
    docker_rules = """
    -p tcp -m conntrack --ctorigdstport 8404 --ctdir ORIGINAL -j DROP
    -p tcp -m conntrack --ctorigdstport 27017 --ctdir ORIGINAL -j DROP
    -p tcp -m conntrack --ctorigdstport 27001 --ctdir ORIGINAL -j DROP
    """
    ifaces = [iface for iface in c.run('ls /sys/class/net', hide=True).stdout.strip().split() if iface.startswith('enp') or iface.startswith('eth')]
    docker_lines = list()
    for rule in docker_rules.strip().split('\n'):
        rule = rule.strip()
        for iface in ifaces:
            do_del = c.run(f'iptables -C DOCKER-USER -i {iface} {rule}', warn=True, hide=True).ok
            c.run(f'iptables -A DOCKER-USER -i {iface} {rule}')
            if do_del:
                c.run(f'iptables -D DOCKER-USER -i {iface} {rule}')
            else:
                print(f'Adding rule v4: DOCKER-USER -i {iface} {rule}')
            docker_lines.append(f'-A DOCKER-USER -i {iface} {rule}')
    do_del = c.run('iptables -C DOCKER-USER -j RETURN', warn=True, hide=True).ok
    c.run('iptables -A DOCKER-USER -j RETURN')
    docker_lines.append('-A DOCKER-USER -j RETURN')
    if do_del:
        c.run('iptables -D DOCKER-USER -j RETURN')
    return docker_lines


def deploy_mongodb_pre(c):
    install_apt_package(c, 'curl')
    install_docker(c)
    systemctl_start_docker(c)
    docker_pull(c, mongodb_image)
    create_directorys_mongodb(c)
    backup_mongodb(c)


def deploy_mongodb_post(c):
    docker_prune(c)


@task(name='deploy-mongodb')
def deploy_mongodb(c):
    deploy_mongodb_pre(c)

    systemctl_stop(c, mongodb_service)
    systemctl_install_service(c, 'docker.service', mongodb_service, [
        ('__execstartpre__', ''),
        ('__additional__', ''),
        ('__storage__', storagedir_mongo + ':/data/db'),
        ('__port__', '27017:27017'),
        ('__image__', mongodb_image)
    ])
    c.run('systemctl daemon-reload')
    systemctl_start(c, mongodb_service)

    deploy_mongodb_post(c)


def deploy_lpos_pre(c):
    install_apt_package(c, 'rsync')
    install_apt_package(c, 'rsyslog')
    install_apt_package(c, 'python3')
    install_apt_package(c, 'virtualenv')
    install_apt_package(c, 'git')
    docker_pull(c, alpine_image)
    docker_pull(c, dns_image)
    docker_pull(c, dhcp_image)
    create_directorys_lpos(c)


@task(name='deploy-lpos')
def deploy_lpos(c):
    deploy_lpos_pre(c)

    systemctl_stop(c, lpos_service)
    upload_project_files(c)
    setup_virtualenv(c, project_dir)
    prepare_lpos_cli(c)
    install_rsyslog(c)
    install_logrotate(c)
    systemctl_install_service(c, 'lpos.service', lpos_service, [('__project_dir__', project_dir)])
    c.run('systemctl daemon-reload')
    systemctl_start(c, lpos_service)


@task(name='deploy-haproxy')
def deploy_haproxy(c):
    install_apt_package(c, 'curl')
    install_docker(c)
    systemctl_start_docker(c)
    docker_pull(c, alpine_image)
    docker_pull(c, haproxy_image)
    systemctl_stop(c, haproxy_service)

    lpos_config = c.run('lpos --config', warn=True, hide=True)
    if not lpos_config.ok:
        print("LPOS not installed, can't setup HAproxy")
        return
    lpos_config = json.loads(lpos_config.stdout)
    if int(lpos_config['server']['port']) == 80:
        print("LPOS allready occupying port 80, can't setup HAproxy")
        return
    c.run(f'mkdir -p {os.path.dirname(haproxy_config)}', hide=True)
    c.put('install/haproxy.cfg', remote=haproxy_config)
    c.run(f"sed -i 's/local_lpos host.docker.internal:[0-9]*/local_lpos host.docker.internal:{lpos_config['server']['port']}/' {haproxy_config}")

    systemctl_install_service(c, 'docker.service', haproxy_service, [
        ('__execstartpre__', '\\n'.join([
            'ExecStartPre=/usr/bin/docker run --rm --name copier-haproxy -v %n:/app -d alpine sleep 3',
            f'ExecStartPre=/usr/bin/docker cp {haproxy_config} copier-haproxy:/app/'])),
        ('__additional__', '--add-host=host.docker.internal:host-gateway --sysctl net.ipv4.ip_unprivileged_port_start=0'),
        ('__storage__', '%n:/usr/local/etc/haproxy/'),
        ('__port__', '80:80 -p 8404:8404 -p 127.0.0.1:5555:5555'),
        ('__image__', haproxy_image)
    ])
    c.run('systemctl daemon-reload')
    systemctl_start(c, haproxy_service)
    docker_prune(c)


@task(name='deploy-iptables')
def deploy_iptables(c):
    c.run('echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections')
    c.run('echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections')
    install_apt_package(c, 'iptables-persistent')

    rules_v4 = """
    INPUT -i lo -j ACCEPT
    INPUT -p tcp -m tcp --dport 22 -j ACCEPT
    INPUT -p tcp -m tcp --dport 80 -j ACCEPT
    INPUT -i docker0 -p tcp -m tcp --dport 8000 -j ACCEPT
    INPUT -p icmp -j ACCEPT
    INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    """
    for rule in rules_v4.strip().split('\n'):
        rule = rule.strip()
        if not c.run(f'iptables -C {rule}', hide=True, warn=True).ok:
            print(f'Adding rule v4: {rule}')
            c.run(f'iptables -A {rule}')
    c.run('iptables -P INPUT DROP')
    c.run('iptables -P FORWARD DROP')

    rules_v6 = """
    INPUT -i lo -j ACCEPT
    INPUT -p tcp -m tcp --dport 22 -j ACCEPT
    INPUT -p icmp -j ACCEPT
    INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    """
    for rule in rules_v6.strip().split('\n'):
        rule = rule.strip()
        if not c.run(f'ip6tables -C {rule}', hide=True, warn=True).ok:
            print(f'Adding rule v6: {rule}')
            c.run(f'ip6tables -A {rule}')
    c.run('ip6tables -P INPUT DROP')
    c.run('ip6tables -P FORWARD DROP')

    docker_lines = reassign_docker_iptables_rules(c)

    print('Writing /etc/iptables/rules.v4')
    c.run(f'mv /etc/iptables/rules.v4 /etc/iptables/rules.v4.bak.{int(time.time())}', hide=True, warn=True)
    c.put('install/iptables.v4', remote='/etc/iptables/rules.v4')
    c.run("sed -i -e 's/###DOCKER_RULES###/" + '\\n'.join(docker_lines) + "/g' /etc/iptables/rules.v4")

    print('Writing /etc/iptables/rules.v6')
    c.run(f'mv /etc/iptables/rules.v6 /etc/iptables/rules.v6.bak.{int(time.time())}', hide=True, warn=True)
    c.put('install/iptables.v6', remote='/etc/iptables/rules.v6')


@task(name='deploy-monitoring')
def deploy_monitoring(c):
    iptables_rules = list()
    ifaces = [iface for iface in c.run('ls /sys/class/net', hide=True).stdout.strip().split() if iface.startswith('enp') or iface.startswith('eth')]

    # ask for ip of monitoring server
    monitoring_ip = input('IP of monitoring server: ').strip()

    # enable LPOS metrics endpoint
    lpos_config = json.loads(c.run('lpos --config', hide=True).stdout)
    if not lpos_config.get('metrics', dict()).get('enabled', False):
        print('Enableing LPOS metrics-endpoint')
        c.run('lpos --enablemetrics', hide=True)
        systemctl_start(c, lpos_service)  # restarts the service
    iptables_rules.append(f"INPUT -p tcp -m tcp -s {monitoring_ip} --dport {lpos_config['metrics']['port']} -j ACCEPT")

    # install prometheus node_exporter
    install_apt_package(c, 'prometheus-node-exporter')
    iptables_rules.append(f'INPUT -p tcp -m tcp -s {monitoring_ip} --dport 9100 -j ACCEPT')

    # install mongodb_exporter (if mongodb on same host)
    if c.run(f'systemctl is-active {mongodb_service}', warn=True, hide=True).ok:
        docker_pull(c, mongoexporter_image)
        systemctl_install_service(c, 'docker.service', mongoexporter_service, [
            ('__execstartpre__', ''),
            ('__additional__', f'--link {mongodb_service}'),
            ('__storage__', '/dev/null:/mnt/dummy:ro'),
            ('__port__', '9216:9216'),
            ('__image__', f'{mongoexporter_image} --mongodb.uri=mongodb://{mongodb_service}:27017/admin --discovering-mode')
        ])
        c.run('systemctl daemon-reload')
        systemctl_start(c, mongoexporter_service)
        docker_prune(c)
        for iface in ifaces:
            iptables_rules.append(f'DOCKER-USER -i {iface} -p tcp -s {monitoring_ip} -m conntrack --ctorigdstport 9216 --ctdir ORIGINAL -j ACCEPT')
            iptables_rules.append(f'DOCKER-USER -i {iface} -p tcp -m conntrack --ctorigdstport 9216 --ctdir ORIGINAL -j DROP')

    # check if haproxy metrics are enabled
    if c.run(f'systemctl is-active {haproxy_service}', warn=True, hide=True).ok:
        haproxy_ports = list()
        for port in c.run(f'docker port {haproxy_service}', hide=True).stdout.strip().split('\n'):
            port = port.strip().split('/', 1)[0]
            if not port == '80' and port not in haproxy_ports:
                haproxy_ports.append(port)
        for port in haproxy_ports:
            for iface in ifaces:
                iptables_rules.append(f'DOCKER-USER -i {iface} -p tcp -s {monitoring_ip} -m conntrack --ctorigdstport {port} --ctdir ORIGINAL -j ACCEPT')

    # add iptables rules
    iptables_lines = list()
    for rule in iptables_rules:
        rule = rule.strip()
        if not c.run(f'iptables -C {rule}', hide=True, warn=True).ok:
            print(f'Adding rule v4: {rule}')
            c.run(f'iptables -A {rule}')
        iptables_lines.append(f'-A {rule}')
    reassign_docker_iptables_rules(c)
    print()
    print()
    print('Please ensure the following lines are added to /etc/iptables/rules.v4:')
    print()
    for line in iptables_lines:
        print(line)


@task
def deploy(c):
    deploy_mongodb_pre(c)
    deploy_lpos_pre(c)

    systemctl_stop(c, lpos_service)
    systemctl_stop(c, mongodb_service)
    upload_project_files(c)
    setup_virtualenv(c, project_dir)
    prepare_lpos_cli(c)
    install_rsyslog(c)
    install_logrotate(c)
    systemctl_install_service(c, 'lpos.service', lpos_service, [('__project_dir__', project_dir)])
    systemctl_install_service(c, 'docker.service', mongodb_service, [
        ('__execstartpre__', ''),
        ('__additional__', ''),
        ('__storage__', storagedir_mongo + ':/data/db'),
        ('__port__', '27017:27017'),
        ('__image__', mongodb_image)
    ])
    c.run('systemctl daemon-reload')
    systemctl_start(c, mongodb_service)
    systemctl_start(c, lpos_service)

    deploy_mongodb_post(c)
