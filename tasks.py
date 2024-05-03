import os
from invoke import task


@task(name='dev-start')
def start_development(c):
    r = c.run('sudo docker ps -f name=dev-mongo', hide=True)
    if 'dev-mongo' not in r.stdout:
        print('Starting mongoDB')
        c.run('sudo docker run --name dev-mongo --rm -p 27017:27017 -d mongo:4.4')
    r = c.run('sudo docker ps -f name=dev-haproxy', hide=True)
    if 'dev-haproxy' not in r.stdout:
        print('Starting HAproxy')
        haproxycfg = os.path.join(os.path.abspath('.'), 'install/haproxy.cfg')
        c.run('sudo docker run --rm --name copier-haproxy -v dev-haproxy:/app -d alpine sleep 3')
        c.run(f'sudo docker cp {haproxycfg} copier-haproxy:/app/')
        cmd = [
            'sudo docker run --name dev-haproxy --rm',
            '--add-host=host.docker.internal:host-gateway --sysctl net.ipv4.ip_unprivileged_port_start=0',
            '-v dev-haproxy:/usr/local/etc/haproxy/ -p 80:80 -p 8404:8404 -p 5555:5555 -d haproxytech/haproxy-alpine:latest'
        ]
        c.run(' '.join(cmd))


@task(name='dev-stop')
def stop_development(c):
    for name in ['dev-haproxy', 'dev-mongo']:
        r = c.run(f'sudo docker ps -f name={name}', hide=True)
        if name in r.stdout:
            print(f'Stopping {name}')
            c.run(f'sudo docker stop {name}')
    print('Removing volumes:')
    c.run('sudo docker volume rm dev-haproxy')


@task(pre=[stop_development], post=[start_development], name='dev-clean')
def cleanup_development(c):
    pass


@task(name='ng-build')
def ng_build(c):
    c.run('rm -rf backend/static/ang')
    c.run('cd frontend; ng build --output-path ../backend/static/ang')
    c.run('cp backend/static/connecttest.txt backend/static/ang/en')


@task(pre=[ng_build], name='create-bundle')
def create_bundle(c):
    c.run('rm -rf /tmp/lpos; mkdir -p /tmp/lpos/backend')
    c.run('rm -rf backend/elements/__pycache__; rm -rf backend/endpoints/__pycache__; rm -rf backend/helpers/__pycache__; rm -rf backend/MTSwitch/__pycache__')
    for item in ['main.py', 'cli.py', 'requirements.txt', 'elements', 'endpoints', 'helpers', 'MTSwitch', 'static']:
        c.run(f'cp -r backend/{item} /tmp/lpos/backend/')
    for item in ['fabfile.py', 'install']:
        c.run(f'cp -r {item} /tmp/lpos/')
    version = c.run('git describe')
    version = version.stdout.strip().replace('v', '', 1).rsplit('-', 1)[0].replace('-', '.')
    with open('/tmp/lpos/backend/helpers/version.py', 'w') as f:
        f.write(f"version = '{version}'")
    c.run('cp install/bundle-installer.sh /tmp/lpos/installer.sh; chmod +x /tmp/lpos/installer.sh')
    c.run(f'makeself /tmp/lpos ./lpos-installer_v{version}.run "Installer for LPOS - LanPartyOnboardingSystem" ./installer.sh')
    c.run('rm -rf /tmp/lpos')
