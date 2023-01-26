from invoke import task


@task(name='dev-start')
def start_development(c):
    r = c.run('sudo docker ps -f name=dev-mongo', hide=True)
    if 'dev-mongo' not in r.stdout:
        print('Starting mongoDB')
        c.run('sudo docker run --name dev-mongo --rm -p 27017:27017 -d mongo:6.0')


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
