import logging
from helpers.backgroundworker import device_scanner, device_onboarding_start

logging.basicConfig(format='%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z', level='INFO')

device_onboarding_start()
device_scanner()
