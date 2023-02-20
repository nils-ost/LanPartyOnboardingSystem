from invoke import task
from elements import Participant


@task(name='coverage')
def coverage(c):
    c.run('coverage erase && coverage run --concurrency=multiprocessing -m unittest discover; coverage combine && coverage html && coverage report')


@task(name='create-admin')
def create_admin(c):
    p = Participant.get_by_login('admin')
    if p is None:
        p = Participant()
    p['login'] = 'admin'
    p['pw'] = 'password'
    p['admin'] = True
    p.save()
