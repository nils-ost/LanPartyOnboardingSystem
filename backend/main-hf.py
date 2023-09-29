import logging
from helpers.backgroundworker import device_scanner

logging.basicConfig(format='%(asctime)s:  %(levelname)s:%(name)s:%(message)s', level='INFO')

device_scanner()
