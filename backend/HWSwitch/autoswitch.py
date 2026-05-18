import logging
import requests
from .baseswitch import BaseSwitch
from .dummyswitch import DummySwitch
from .mikrotikswitch import MikroTikSwitch


class AutoDetectSwitch(BaseSwitch):
    def __init__(self, host, user, password):
        self.logger = logging.getLogger('AutoDetectSwitch')
        r = ''
        try:
            r = requests.get(f'http://{host}').text
        except Exception:
            pass

        if r == 'nils_ost - dummy switch':
            self.logger.info(f"Detected DummySwitch for host '{host}'")
            self.__class__ = DummySwitch
        else:
            self.logger.info(f"Defaulting to MikroTikSwitch for host '{host}'")
            self.__class__ = MikroTikSwitch

        self.__init__(host, user, password)
