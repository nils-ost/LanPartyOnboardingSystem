import logging


class SwitchPort():
    logger = logging.getLogger('SwitchPort')

    def __init__(self):
        self.idx = None
        self.name = ''
        self.type = ''
        self.enabled = False
        self.link = False
        self.speed = None
        self._fwd = list()
        self.hosts = list()
        self.vlan_mode = ''
        self.vlan_receive = ''
        self.vlan_default = 0
        self.vlan_force = False

    def fwdTo(self, port):
        if isinstance(port, self.__class__):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error(f'fwdTo: port is not an instance of int or {self.__class__.__name__}')
            return False

        if port == self.idx:
            return False
        if port not in self._fwd:
            self._fwd.append(port)
            return True
        return False

    def fwdNotTo(self, port):
        if isinstance(port, self.__class__):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error(f'fwdNotTo: port is not an instance of int or {self.__class__.__name__}')
            return False

        if port in self._fwd:
            self._fwd.remove(port)
            return True
        return False


class SwitchVLAN():
    logger = logging.getLogger('SwitchVLAN')

    def __init__(self):
        self.id = None
        self.isolation = False
        self.learning = False
        self.mirror = False
        self.igmp = False
        self._member = list()

    def memberAdd(self, port):
        if isinstance(port, SwitchPort):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error('memberAdd: port is not an instance of int or SwitchPort')
            return False

        if port not in self._member:
            self._member.append(port)
            return True
        return False

    def memberRemove(self, port):
        if isinstance(port, SwitchPort):
            port = port.idx
        elif not isinstance(port, int):
            self.logger.error('memberRemove: port is not an instance of int or SwitchPort')
            return False

        if port in self._member:
            self._member.remove(port)
            return True
        return False
