import logging
from MTSwitch import MikroTikSwitch
import json

logging.basicConfig(format='%(levelname)s:%(name)s:%(message)s', level='INFO')

config = json.load(open('config.json', 'r'))
mts = MikroTikSwitch(config['host'], config['user'], config['pw'])
p = mts.ports[-1]
print(p.name, p.type, p.vlan_default)
print(mts._pending_commits)
mts.portEdit(p, vdefault=1)
mts.vlanEdit(2, memberRemove=27)
print(p.name, p.type, p.vlan_default)
print(mts._pending_commits)
mts.commitNeeded()
print(mts._pending_commits)
