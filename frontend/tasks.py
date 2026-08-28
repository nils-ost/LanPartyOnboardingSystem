from invoke import task


@task(name='container-image-build')
def build_container_image(c, version=None, beta=False, alpha=False):
    image = 'nilsost/lpos-frontend'
    tags = ''
    if version is not None:
        tags += f' -t {image}:{version}'
    if alpha:
        tags += f' -t {image}:alpha'
    elif beta:
        tags += f' -t {image}:beta'
    else:
        tags += f' -t {image}:latest'
    c.run(f'sudo docker buildx build --platform linux/amd64{tags} --load .')


@task(name='container-image-push')
def push_container_image(c, version=None, beta=False, alpha=False):
    image = 'nilsost/lpos-frontend'
    tags = ''
    if version is not None:
        tags += f' -t {image}:{version}'
    if alpha:
        tags += f' -t {image}:alpha'
    elif beta:
        tags += f' -t {image}:beta'
    else:
        tags += f' -t {image}:latest'
    c.run(f'sudo docker buildx build --platform linux/amd64,linux/arm64{tags} --push .')
