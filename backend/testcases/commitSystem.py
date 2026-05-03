import unittest
from noapiframe import docDB
from elements import Setting, Switch, VLAN, IpPool
from helpers.backgroundworker import device_scanner_scan_once


def setUpModule():
    docDB.clear()
    Setting.set('disable_auto_commits', True)
    Setting.set('absolute_seatnumbers', True)
    Setting.set('os_nw_interface', 'lpos0')
    Setting.set('play_ip', IpPool.octetts_to_int(192, 168, 123, 4))
    Setting.set('play_dhcp', '192.168.123.3')
    Setting.set('play_gateway', '192.168.123.1')
    Setting.set('upstream_dns', '192.168.123.2')
    Setting.set('domain', 'nlpt.network')
    Setting.set('subdomain', 'onboarding')
    Switch({'desc': 'dummy1', 'addr': 'localhost:1337', 'purpose': 0}).save()
    mgmt_vlan_id = VLAN({'desc': 'mgmt', 'number': 113, 'purpose': 1}).save()['created']
    play_vlan_id = VLAN({'desc': 'mgmt', 'number': 112, 'purpose': 0}).save()['created']
    IpPool({
        'desc': 'mgmt', 'vlan_id': mgmt_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(10, 14, 66, 1),
        'range_end': IpPool.octetts_to_int(10, 14, 66, 254)}).save()
    IpPool({
        'desc': 't1', 'vlan_id': play_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(192, 168, 123, 10),
        'range_end': IpPool.octetts_to_int(192, 168, 123, 19)}).save()
    IpPool({
        'desc': 't2', 'vlan_id': play_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(192, 168, 123, 20),
        'range_end': IpPool.octetts_to_int(192, 168, 123, 29)}).save()
    device_scanner_scan_once()


setup_module = setUpModule


class TestCommitSystem(unittest.TestCase):
    def test_integrity(self):
        from helpers.system import check_integrity
        r = check_integrity()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])
