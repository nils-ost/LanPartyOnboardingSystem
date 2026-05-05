import unittest
import requests
from noapiframe import docDB
from elements import Setting, Switch, VLAN, IpPool, Port
from helpers.backgroundworker import device_scanner_scan_once


switch_hw_config = {
    'c1': {
        'system': {'identity': 'dummy - c1', 'mac_addr': '112233445561'},
        'ports': {'gbe-count': 1, 'sfp-count': 8},
        'hosts': [
            {'port': 1, 'addr': '112233445562'},
            {'port': 2, 'addr': '112233445563'},
            {'port': 3, 'addr': '112233445564'},
        ]
    },
    'c2': {
        'system': {'identity': 'dummy - c2', 'mac_addr': '112233445562'},
        'ports': {'gbe-count': 8, 'sfp-count': 2},
        'hosts': [
            {'port': 0, 'addr': '1234567890ab'},
            {'port': 8, 'addr': '112233445561'},
            {'port': 8, 'addr': '112233445563'},
            {'port': 8, 'addr': '112233445564'},
        ]
    },
    'p1': {
        'system': {'identity': 'dummy - p1', 'mac_addr': '112233445563'},
        'ports': {'gbe-count': 16, 'sfp-count': 2},
        'hosts': [
            {'port': 16, 'addr': '112233445561'},
            {'port': 16, 'addr': '112233445562'},
            {'port': 16, 'addr': '112233445564'},
        ]
    },
    'p2': {
        'system': {'identity': 'dummy - p2', 'mac_addr': '112233445564'},
        'ports': {'gbe-count': 16, 'sfp-count': 2},
        'hosts': [
            {'port': 16, 'addr': '112233445561'},
            {'port': 16, 'addr': '112233445562'},
            {'port': 16, 'addr': '112233445563'},
        ]
    }
}


def setUpModule():
    # "programming" switch hardware
    requests.post('http://localhost:1337/config/', json=switch_hw_config['c1'])
    requests.post('http://localhost:1338/config/', json=switch_hw_config['c2'])
    requests.post('http://localhost:1339/config/', json=switch_hw_config['p1'])
    requests.post('http://localhost:1340/config/', json=switch_hw_config['p2'])
    # resetting DB for a clean run
    docDB.clear()
    # configuring global settings
    Setting.set('disable_auto_commits', True)
    Setting.set('absolute_seatnumbers', True)
    Setting.set('os_nw_interface', 'lpos0')
    Setting.set('play_ip', IpPool.octetts_to_int(192, 168, 123, 4))
    Setting.set('play_dhcp', '192.168.123.3')
    Setting.set('play_gateway', '192.168.123.1')
    Setting.set('upstream_dns', '192.168.123.2')
    Setting.set('domain', 'nlpt.network')
    Setting.set('subdomain', 'onboarding')
    Setting.set('nlpt_sso', True)
    Setting.set('sso_login_url', 'https://nlpt.online/login')
    Setting.set('sso_onboarding_url', 'https://nlpt.online/onboard')
    Setting.set('sso_ip_overwrite', '1.2.3.4')
    # creating VLANs
    mgmt_vlan_id = VLAN({'desc': 'mgmt', 'number': 113, 'purpose': 1}).save()['created']
    play_vlan_id = VLAN({'desc': 'play', 'number': 112, 'purpose': 0}).save()['created']
    t1_ob_vlan_id = VLAN({'desc': 't1 ob', 'number': 121, 'purpose': 2}).save()['created']
    t2_ob_vlan_id = VLAN({'desc': 't2 ob', 'number': 122, 'purpose': 2}).save()['created']
    # creating Switches
    c1_switch_id = Switch({'desc': 'C1', 'addr': 'localhost:1337', 'purpose': 0}).save()['created']
    c2_switch_id = Switch({'desc': 'C2', 'addr': 'localhost:1338', 'purpose': 0}).save()['created']
    p1_switch_id = Switch({'desc': 'P1', 'addr': 'localhost:1339', 'purpose': 1, 'onboarding_vlan_id': t1_ob_vlan_id}).save()['created']
    p2_switch_id = Switch({'desc': 'P2', 'addr': 'localhost:1340', 'purpose': 1, 'onboarding_vlan_id': t2_ob_vlan_id}).save()['created']
    # creating required IpPools
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
    IpPool({
        'desc': 't1 ob', 'vlan_id': t1_ob_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(172, 16, 1, 10),
        'range_end': IpPool.octetts_to_int(172, 16, 1, 99)}).save()
    IpPool({
        'desc': 't2 ob', 'vlan_id': t2_ob_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(172, 16, 2, 10),
        'range_end': IpPool.octetts_to_int(172, 16, 2, 99)}).save()
    # scan switch ports for hosts
    device_scanner_scan_once()
    # connecting the switches together with switchlinks
    p = Port.get_by_number(c1_switch_id, 1)
    p['switchlink_port_id'] = Port.get_by_number(c2_switch_id, 8)['_id']
    p.save()
    p = Port.get_by_number(c1_switch_id, 2)
    p['switchlink_port_id'] = Port.get_by_number(p1_switch_id, 16)['_id']
    p.save()
    p = Port.get_by_number(c1_switch_id, 3)
    p['switchlink_port_id'] = Port.get_by_number(p2_switch_id, 16)['_id']
    p.save()


setup_module = setUpModule


class TestCommitSystem(unittest.TestCase):
    def test_integrity(self):
        from helpers.system import check_integrity
        r = check_integrity()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])

    def test_commit_everyting(self):
        from helpers.vlanmgmt import vlan_os_interfaces_commit, vlan_dns_server_commit, vlan_dhcp_server_commit
        from helpers.switchmgmt import switches_commit
        from helpers.haproxy import ssoHAproxy, lposHAproxy

        # haproxy
        if Setting.value('nlpt_sso'):
            self.assertTrue(ssoHAproxy.start_container())
            ssoHAproxy.wait_for_running()
            self.assertTrue(ssoHAproxy.setup_sso_ip())
        self.assertTrue(lposHAproxy.set_ms_redirect_url())
        # switches
        r = switches_commit()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])
        # interfaces
        r = vlan_os_interfaces_commit()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])
        # dns
        r = vlan_dns_server_commit()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])
        # dhcp
        r = vlan_dhcp_server_commit()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])

    def test_retreat_everyting(self):
        from helpers.switchmgmt import switches_retreat
        from helpers.vlanmgmt import vlan_os_interfaces_retreat, vlan_dns_server_retreat, vlan_dhcp_server_retreat
        # first retreat everything, then do the checks, to have retreated as much as possible
        r_dhcp = vlan_dhcp_server_retreat()
        r_dns = vlan_dns_server_retreat()
        r_int = vlan_os_interfaces_retreat()
        r_swi = switches_retreat()
        self.assertIn('code', r_dhcp)
        self.assertEqual(r_dhcp['code'], 0, r_dhcp['desc'])
        self.assertIn('code', r_dns)
        self.assertEqual(r_dns['code'], 0, r_dns['desc'])
        self.assertIn('code', r_int)
        self.assertEqual(r_int['code'], 0, r_int['desc'])
        self.assertIn('code', r_swi)
        self.assertEqual(r_swi['code'], 0, r_swi['desc'])

    def test_no_docker_remains_after_retreat(self):
        """
        after system is retreated no docker elements should exist: container, networks, volumes (starting with lpos-)
        """
        pass
