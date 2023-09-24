from invoke import task


@task(name='dev-start')
def start_development(c):
    r = c.run('sudo docker ps -f name=dev-mongo', hide=True)
    if 'dev-mongo' not in r.stdout:
        print('Starting mongoDB')
        c.run('sudo docker run --name dev-mongo --rm -p 27017:27017 -d mongo:4.4')


@task(name='dev-stop')
def stop_development(c):
    for name in ['dev-mongo']:
        r = c.run(f'sudo docker ps -f name={name}', hide=True)
        if name in r.stdout:
            print(f'Stopping {name}')
            c.run(f'sudo docker stop {name}')


@task(pre=[stop_development], post=[start_development], name='dev-clean')
def cleanup_development(c):
    pass


@task(name='nlpt-onb')
def extract_nlpt_onboarding(c):
    c.run('sudo docker pull ghcr.io/nlptournament/nlpt-onboarding:main')
    c.run('sudo docker run --rm --name extract-onb -d ghcr.io/nlptournament/nlpt-onboarding:main')
    c.run('sudo docker cp extract-onb:/usr/share/nginx/html backend/static/ang/')
    c.run('sudo chown -R 1000:1000 backend/static/ang/html; mv backend/static/ang/html backend/static/ang/onb')
    c.run('sudo docker stop extract-onb')


@task(name='ng-build', post=[extract_nlpt_onboarding])
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
