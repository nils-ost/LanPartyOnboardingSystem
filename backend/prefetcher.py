import logging
import docker
import tempfile
import sys


docker_images = {
    'alpine': 'alpine:latest',
    'python': 'python:3.10-alpine',
    'haproxy': 'haproxytech/haproxy-alpine:2.9.6',
    'coredns': 'coredns/coredns:1.11.1',
    'kea-dhcp4': 'docker.cloudsmith.io/isc/docker/kea-dhcp4:2.5.7'
}


_LPOS_PSUTIL_HELPER = f"""
FROM {docker_images['python']}
LABEL org.opencontainers.image.authors="LPOS"
RUN pip3 install psutil
"""


docker_build_images = {
    'psutil': {'tag': 'lpos-psutil-helper:v1', 'dockerfile': _LPOS_PSUTIL_HELPER}
}


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z', level='INFO')
    logger = logging.getLogger('prefetcher')
    dcli = docker.from_env()
    error_pull = False
    for image in docker_images.values():
        logger.info(f'Prefetching docker image: {image}')
        try:
            dcli.images.get(image)
            logger.info(f'Image already present: {image}')
        except docker.errors.ImageNotFound:
            try:
                dcli.images.pull(image)
                logger.info(f'Pulled image: {image}')
            except Exception as e:
                logger.error(f'Error pulling image "{image}": {e}')
                error_pull = True

    error_build = False
    for shortname, image in docker_build_images.items():
        if len(dcli.images.list(name=image['tag'])) == 1:
            logger.info(f'Image already build: {image["tag"]}')
            docker_build_images[shortname] = image['tag']
            continue
        try:
            with tempfile.TemporaryFile() as dockerfile:
                dockerfile.write(image['dockerfile'])
                dockerfile.flush()
                dockerfile.seek(0)
                dcli.images.build(fileobj=dockerfile, tag=image['tag'])
                docker_build_images[shortname] = image['tag']
                logger.info(f'Build image. {image["tag"]}')
        except Exception as e:
            logger.error(f'Error building image "{image["tag"]}": {e}')
            error_build = True

    if error_pull:
        logger.warning('Prefetch finished with errors!')
    else:
        logger.info('Prefetch finished.')

    if error_build:
        logger.warning('Build finished with errors!')
    else:
        logger.info('Build finished.')

    if error_pull or error_build:
        sys.exit(1)
    else:
        sys.exit(0)
