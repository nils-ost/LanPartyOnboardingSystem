import os
import psutil
from invoke import task

dummy_net_int = 'lpos0'
dummy_net_ip = '10.14.66.4/24'
dummy_net_mac = '12:34:56:78:90:ab'


@task(name='dev-start')
def start_development(c):
    r = c.run('sudo docker ps -f name=dev-mongo', hide=True)
    if 'dev-mongo' not in r.stdout:
        print('Starting mongoDB')
        c.run('sudo docker run --name dev-mongo --rm -p 27017:27017 -d mongo:4.4')
    r = c.run('sudo docker ps -f name=dev-haproxy', hide=True)
    if 'dev-haproxy' not in r.stdout:
        print('Starting HAproxy')
        haproxycfg = os.path.join(os.path.abspath('.'), 'ansible/templates/haproxy.cfg.j2')
        with open('/tmp/haproxy.cfg', 'w') as f:
            content = open(haproxycfg, 'r').read().replace('{{ lpos_port.stdout }}', '8000')
            f.write(content)
        c.run('sudo docker run --rm --name copier-haproxy -v dev-haproxy:/app -d alpine sleep 3')
        c.run('sudo docker cp /tmp/haproxy.cfg copier-haproxy:/app/haproxy.cfg')
        cmd = [
            'sudo docker run --name dev-haproxy --rm --cap-add=NET_ADMIN',
            '--add-host=host.docker.internal:host-gateway --sysctl net.ipv4.ip_unprivileged_port_start=0',
            '-v dev-haproxy:/usr/local/etc/haproxy/ -p 80:80 -p 8404:8404 -p 5555:5555 -d haproxytech/haproxy-alpine:2.9.6'
        ]
        c.run(' '.join(cmd))
    for i in range(4):
        r = c.run(f'sudo docker ps -f name=dev-dummyswitch-{i}', hide=True)
        if f'dev-dummyswitch-{i}' not in r.stdout:
            print(f'Starting dummy-switch-{i}')
            cmd = [
                f'sudo docker run --name dev-dummyswitch-{i} --rm',
                f'-v ./backend/:/app:ro -p 13{37 + i}:1337 -d python:3.10-alpine',
                '/bin/sh -c "pip3 install CherryPy cherrypy-cors; python3 /app/dummyswitch.py"'
            ]
            c.run(' '.join(cmd))
    if dummy_net_int not in psutil.net_if_addrs().keys():
        print('Configuring dummy network interface')
        c.run('sudo modprobe dummy')
        c.run(f'sudo ip link add {dummy_net_int} type dummy')
        c.run(f'sudo ifconfig {dummy_net_int} hw ether {dummy_net_mac}')
        c.run(f'sudo ip a add {dummy_net_ip} dev {dummy_net_int}')
        c.run(f'sudo ip link set dev {dummy_net_int} up')
        print(f"\nfor testing commits you can now use the interface '{dummy_net_int}' with IP '{dummy_net_ip}' and MAC '{dummy_net_mac}'")


@task(name='dev-stop')
def stop_development(c):
    for i in range(4):
        name = f'dev-dummyswitch-{i}'
        r = c.run(f'sudo docker ps -f name={name}', hide=True)
        if name in r.stdout:
            print(f'Stopping {name}')
            c.run(f'sudo docker stop {name}')
    for name in ['dev-haproxy', 'dev-mongo']:
        r = c.run(f'sudo docker ps -f name={name}', hide=True)
        if name in r.stdout:
            print(f'Stopping {name}')
            c.run(f'sudo docker stop {name}')
    print('Removing volumes:')
    try:
        c.run('sudo docker volume rm dev-haproxy')
    except Exception:
        pass
    if dummy_net_int in psutil.net_if_addrs().keys():
        print('Removing dummy network interface')
        c.run(f'sudo ip a del {dummy_net_ip} dev {dummy_net_int}')
        c.run(f'sudo ip link delete {dummy_net_int} type dummy')
        c.run('sudo rmmod dummy')


@task(pre=[stop_development], post=[start_development], name='dev-clean')
def cleanup_development(c):
    pass


@task(name='ng-build')
def ng_build(c):
    c.run('rm -rf backend/static/ang')
    c.run('cd frontend; ng build --output-path ../backend/static/ang')
    c.run('cp backend/static/connecttest.txt backend/static/ang/en')
    c.run('cp backend/static/connecttest.txt backend/static/ang/de')


@task(pre=[ng_build], name='create-bundle')
def create_bundle(c):
    c.run('rm -rf /tmp/lpos; mkdir -p /tmp/lpos/backend')
    c.run('rm -rf backend/elements/__pycache__; rm -rf backend/endpoints/__pycache__; rm -rf backend/helpers/__pycache__; rm -rf backend/HWSwitch/__pycache__')
    for item in ['main.py', 'scanner.py', 'cli.py', 'requirements.txt', 'elements', 'endpoints', 'helpers', 'HWSwitch', 'static']:
        c.run(f'cp -r backend/{item} /tmp/lpos/backend/')
    for item in ['ansible']:
        c.run(f'cp -r {item} /tmp/lpos/')
    version = c.run('git describe')
    version = version.stdout.strip().replace('v', '', 1).rsplit('-', 1)[0].replace('-', '.')
    with open('/tmp/lpos/backend/helpers/version.py', 'w') as f:
        f.write(f"version = '{version}'")
    c.run('mv /tmp/lpos/ansible/bundle-installer.sh /tmp/lpos/installer.sh; chmod +x /tmp/lpos/installer.sh')
    c.run(f'makeself /tmp/lpos ./lpos-installer_v{version}.run "Installer for LPOS - LanPartyOnboardingSystem" ./installer.sh')
    c.run('rm -rf /tmp/lpos')


@task(name='container-images-build', aliases=['cib', ])
def build_container_images(c):
    version = c.run('git describe', warn=True, hide=True)
    version_arg = ''
    if version.return_code > 0:
        version = None
    else:
        version = version.stdout.strip().replace('v', '', 1)
        if '-' in version:
            version, build = version.rsplit('-', 1)[0].rsplit('-', 1)
            major, minor, _ = version.split('.')
            minor = int(minor) + 1
            branch = c.run('git branch --show-current', warn=True, hide=True).stdout.strip()
            if branch == 'main':
                version = f'{major}.{minor}.0.{build}beta'
                version_arg = f' --version {version} --beta'
            else:
                version = f'{major}.{minor}.0.{build}alpha'
                version_arg = f' --version {version} --alpha'
        else:
            version_arg = f' --version {version}'

    if version:
        with open('backend/helpers/version.py', 'w') as f:
            f.write(f"version = '{version}'")
    c.run(f'cd backend; invoke container-image-build{version_arg}')
    c.run('git restore backend/helpers/version.py')
    c.run(f'cd frontend; invoke container-image-build{version_arg}')
    c.run(f'cd haproxy; invoke container-image-build{version_arg}')


@task(name='container-images-push', aliases=['cip', ])
def push_container_images(c):
    version = c.run('git describe', warn=True, hide=True)
    version_arg = ''
    if version.return_code > 0:
        version = None
    else:
        version = version.stdout.strip().replace('v', '', 1)
        if '-' in version:
            version, build = version.rsplit('-', 1)[0].rsplit('-', 1)
            major, minor, _ = version.split('.')
            minor = int(minor) + 1
            branch = c.run('git branch --show-current', warn=True, hide=True).stdout.strip()
            if branch == 'main':
                version = f'{major}.{minor}.0.{build}beta'
                version_arg = f' --version {version} --beta'
            else:
                version = f'{major}.{minor}.0.{build}alpha'
                version_arg = f' --version {version} --alpha'
        else:
            version_arg = f' --version {version}'

    if version:
        with open('backend/helpers/version.py', 'w') as f:
            f.write(f"version = '{version}'")
    c.run(f'cd backend; invoke container-image-push{version_arg}')
    c.run('git restore backend/helpers/version.py')
    c.run(f'cd frontend; invoke container-image-push{version_arg}')
    c.run(f'cd haproxy; invoke container-image-push{version_arg}')
