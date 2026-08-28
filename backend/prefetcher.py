import logging
import docker
import sys


docker_images = {
    'alpine': 'alpine:latest',
    'python': 'python:3.10-alpine',
    'haproxy': 'haproxytech/haproxy-alpine:2.9.6',
    'coredns': 'coredns/coredns:1.11.1',
    'kea-dhcp4': 'docker.cloudsmith.io/isc/docker/kea-dhcp4:2.5.7'
}


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z', level='INFO')
    logger = logging.getLogger('prefetcher')
    dcli = docker.from_env()
    error = False
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
                error = True
    if error:
        logger.warning('Prefetch finished with errors! Exiting...')
        sys.exit(1)
    else:
        logger.info('Prefetch finished. Exiting...')
        sys.exit(0)
