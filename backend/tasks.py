from invoke import task


@task(name='coverage')
def coverage(c):
    c.run('coverage erase && coverage run --concurrency=multiprocessing -m unittest discover; coverage combine && coverage html && coverage report')
