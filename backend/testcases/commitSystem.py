import unittest
import requests
import docker
import tempfile
import tarfile
import json
from noapiframe import docDB
from elements import Setting, Switch, VLAN, IpPool, Port, Table, Seat, Participant, Device
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
            {'port': 3, 'addr': '11223344aaa1'},
            {'port': 8, 'addr': '11223344aaa2'},
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
    addi_ippool_seats_id = IpPool({
        'desc': 'addi seats', 'vlan_id': play_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(192, 168, 123, 100),
        'range_end': IpPool.octetts_to_int(192, 168, 123, 199)}).save()['created']
    t1_ippool_seats_id = IpPool({
        'desc': 't1 seats', 'vlan_id': play_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(192, 168, 123, 10),
        'range_end': IpPool.octetts_to_int(192, 168, 123, 19)}).save()['created']
    t2_ippool_seats_id = IpPool({
        'desc': 't2 seats', 'vlan_id': play_vlan_id, 'mask': 24,
        'range_start': IpPool.octetts_to_int(192, 168, 123, 20),
        'range_end': IpPool.octetts_to_int(192, 168, 123, 29)}).save()['created']
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
    # create tables
    t1_table_id = Table({
        'number': 1, 'desc': 'T1', 'switch_id': p1_switch_id, 'seat_ip_pool_id': t1_ippool_seats_id, 'add_ip_pool_id': addi_ippool_seats_id
        }).save()['created']
    t2_table_id = Table({
        'number': 2, 'desc': 'T2', 'switch_id': p2_switch_id, 'seat_ip_pool_id': t2_ippool_seats_id, 'add_ip_pool_id': addi_ippool_seats_id
        }).save()['created']
    # create seats
    for i in range(1, 11):
        Seat({'number': i, 'number_absolute': 10 + i, 'pw': '1234', 'table_id': t1_table_id}).save()
        Seat({'number': i, 'number_absolute': 20 + i, 'pw': '1234', 'table_id': t2_table_id}).save()
    # create participants
    Participant({'login': 'part1', 'seat_id': Seat.get_by_number_absolute(21)['_id']}).save()
    Participant({'login': 'part2', 'seat_id': Seat.get_by_number_absolute(23)['_id']}).save()
    # link devices to seats
    d = Device().get_by_mac('11223344aaa1')
    d['seat_id'] = Seat.get_by_number_absolute(21)['_id']
    d.save()
    d = Device().get_by_mac('11223344aaa2')
    d['seat_id'] = Seat.get_by_number_absolute(23)['_id']
    d.save()


setup_module = setUpModule


def docker_get_file_content(container, path, filename):
    with tempfile.TemporaryFile(suffix='.tar') as archive:
        bits, _ = container.get_archive(path)
        for chunk in bits:
            archive.write(chunk)
        archive.flush()
        archive.seek(0)
        with tarfile.open(fileobj=archive, mode='r') as tar:
            m = tar.getmember(filename)
            return tar.extractfile(m).read().decode('utf-8')


class TestCommitSystem(unittest.TestCase):
    def test_000_integrity(self):
        from helpers.system import check_integrity
        r = check_integrity()
        self.assertIn('code', r)
        self.assertEqual(r['code'], 0, r['desc'])

    def test_001_commit_everyting(self):
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

    def test_002_switch_configuration(self):
        """
        tests if Switch(hardware) is configured as planned
        """
        # C1
        sw = requests.get('http://localhost:1337/config/').json()
        self.assertEqual(len(sw['vlans']), 4)
        sw_vlans = {s['id']: s for s in sw['vlans']}
        for i in [113, 112, 121, 122]:
            self.assertIn(i, sw_vlans.keys())
        self.assertEqual(sw_vlans[113]['member'], '0b011100000')
        self.assertEqual(sw_vlans[112]['member'], '0b111111111')
        self.assertEqual(sw_vlans[121]['member'], '0b011100000')
        self.assertEqual(sw_vlans[122]['member'], '0b011100000')
        for i in [1, 2, 3]:  # switchlinks
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only tagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in [0, 4, 5, 6, 7, 8]:  # empty ports
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only untagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in range(9):  # all ports allowed to forward everywhere
            f = '0b' + '1' * i + '0' + '1' * (9 - i - 1)
            self.assertEqual(sw['forward'][f'from{i}'], f)
        # C2
        sw = requests.get('http://localhost:1338/config/').json()
        self.assertEqual(len(sw['vlans']), 4)
        sw_vlans = {s['id']: s for s in sw['vlans']}
        for i in [113, 112, 121, 122]:
            self.assertIn(i, sw_vlans.keys())
        self.assertEqual(sw_vlans[113]['member'], '0b1000000010')
        self.assertEqual(sw_vlans[112]['member'], '0b1111111111')
        self.assertEqual(sw_vlans[121]['member'], '0b1000000010')
        self.assertEqual(sw_vlans[122]['member'], '0b1000000010')
        for i in [0]:  # lpos-host
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'any')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 113)
        for i in [8]:  # switchlinks
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only tagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in [1, 2, 3, 4, 5, 6, 7, 9]:  # empty ports
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only untagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in range(10):  # all ports allowed to forward everywhere
            f = '0b' + '1' * i + '0' + '1' * (10 - i - 1)
            self.assertEqual(sw['forward'][f'from{i}'], f)
        # P1
        sw = requests.get('http://localhost:1339/config/').json()
        self.assertEqual(len(sw['vlans']), 3)
        sw_vlans = {s['id']: s for s in sw['vlans']}
        for i in [113, 112, 121]:
            self.assertIn(i, sw_vlans.keys())
        self.assertEqual(sw_vlans[113]['member'], '0b000000000000000010')
        self.assertEqual(sw_vlans[112]['member'], '0b000000000000000010')
        self.assertEqual(sw_vlans[121]['member'], '0b111111111111111111')
        for i in [16]:  # switchlinks
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only tagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17]:  # empty ports
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only untagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 121)
        for i in [16]:  # switchlink allowed to forward everywhere
            f = '0b111111111111111101'
            self.assertEqual(sw['forward'][f'from{i}'], f)
        for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17]:  # empty ports only allowed to forward to switchlink
            f = '0b000000000000000010'
            self.assertEqual(sw['forward'][f'from{i}'], f)
        # P2
        sw = requests.get('http://localhost:1340/config/').json()
        self.assertEqual(len(sw['vlans']), 3)
        sw_vlans = {s['id']: s for s in sw['vlans']}
        for i in [113, 112, 122]:
            self.assertIn(i, sw_vlans.keys())
        self.assertEqual(sw_vlans[113]['member'], '0b000000000000000010')
        self.assertEqual(sw_vlans[112]['member'], '0b000100001000000010')
        self.assertEqual(sw_vlans[122]['member'], '0b111011110111111111')
        # port vlans
        for i in [16]:  # switchlinks
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only tagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in [3, 8]:  # participant ports
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only untagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 112)
        for i in [0, 1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17]:  # empty ports
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['mode'], 'strict')
            self.assertEqual(sw['ports_vlans'][f'idx{i}']['receive'], 'only untagged')
            self.assertEqual(int(sw['ports_vlans'][f'idx{i}']['default']), 122)
        # forwards
        for i in [3, 8, 16]:  # participants and switchlink allowed to forward everywhere
            f = '0b' + '1' * i + '0' + '1' * (18 - i - 1)
            self.assertEqual(sw['forward'][f'from{i}'], f)
        for i in [0, 1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17]:  # empty ports only allowed to forward to switchlink
            f = '0b000000000000000010'
            self.assertEqual(sw['forward'][f'from{i}'], f)

    def test_010_ipvlans_configuration(self):
        """
        test docker ipvlans (interfaces) exist and are configured correct
        """
        dcli = docker.from_env()
        for i in [113]:
            try:
                dcli.networks.get(f'lpos-ipvlan{i}')
                self.assertTrue(False, f'docker network lpos-ipvlan{i} does exist, but shouldnt')
            except docker.errors.NotFound:
                self.assertTrue(True)
        networks = dict({
            112: '192.168.123.0/24',
            121: '172.16.1.0/24',
            122: '172.16.2.0/24'
        })
        for i in networks.keys():
            try:
                dnet = dcli.networks.get(f'lpos-ipvlan{i}')
            except docker.errors.NotFound:
                self.assertTrue(False, f'docker network lpos-ipvlan{i} does not exist')
            self.assertEqual(dnet.attrs['Driver'], 'ipvlan')
            self.assertEqual(dnet.attrs['EnableIPv4'], True)
            self.assertEqual(dnet.attrs['EnableIPv6'], False)
            self.assertEqual(dnet.attrs['IPAM']['Config'][0]['Subnet'], networks[i])
            self.assertEqual(dnet.attrs['Options']['parent'].split('.')[0], 'lpos0')
            self.assertEqual(len(dnet.attrs['Status']['IPAM']['Subnets']), 1)
            self.assertIn(networks[i], dnet.attrs['Status']['IPAM']['Subnets'])

    def test_020_dhcp_docker_container_config(self):
        """
        test dhcp docker container configuration
        """
        dcli = docker.from_env()
        for i in [113]:
            try:
                dcli.containers.get(f'lpos-ipvlan{i}-dhcp')
                self.assertTrue(False, f'docker container lpos-ipvlan{i}-dhcp does exist, but shouldnt')
            except docker.errors.NotFound:
                self.assertTrue(True)
        containers = dict({
            112: {
                'name': 'lpos-ipvlan112-dhcp',
                'network': 'lpos-ipvlan112',
                'ip': '192.168.123.3'
            },
            121: {
                'name': 'lpos-ipvlan121-dhcp',
                'network': 'lpos-ipvlan121',
                'ip': '172.16.1.13'
            },
            122: {
                'name': 'lpos-ipvlan122-dhcp',
                'network': 'lpos-ipvlan122',
                'ip': '172.16.2.13'
            },
        })
        for i in containers.keys():
            try:
                dcon = dcli.containers.get(containers[i]['name'])
            except docker.errors.NotFound:
                self.assertTrue(False, f"docker container {containers[i]['name']} does not exist")
            self.assertEqual(dcon.status, 'running')
            self.assertEqual(dcon.attrs['HostConfig']['NetworkMode'], containers[i]['network'])
            # test mounts
            for m in dcon.attrs['Mounts']:
                if m['Name'] == containers[i]['name']:
                    self.assertEqual(m['Destination'], '/etc/kea')
                    break
            else:
                self.assertTrue(False, f"could not find required mount in {containers[i]['name']}")
            # test networks
            self.assertEqual(len(dcon.attrs['NetworkSettings']['Networks']), 1)
            self.assertIn(containers[i]['network'], dcon.attrs['NetworkSettings']['Networks'])
            self.assertEqual(dcon.attrs['NetworkSettings']['Networks'][containers[i]['network']]['IPAddress'], containers[i]['ip'])

    def test_035_dhcp_container_content(self):
        """
        test dhcp docker container content (configuration)
        """
        dcli = docker.from_env()
        # ipvlan112
        c = json.loads(docker_get_file_content(dcli.containers.get('lpos-ipvlan112-dhcp'), '/etc/kea', 'kea/kea-dhcp4.conf'))
        self.assertEqual(len(c['Dhcp4']['subnet4']), 1)
        self.assertEqual(c['Dhcp4']['subnet4'][0]['subnet'], '192.168.123.0/24')
        self.assertEqual(len(c['Dhcp4']['subnet4'][0]['pools']), 1)
        self.assertEqual(c['Dhcp4']['subnet4'][0]['pools'][0]['pool'], '192.168.123.100-192.168.123.199')
        self.assertEqual(len(c['Dhcp4']['option-data']), 2)
        options = {o['name']: o['data'] for o in c['Dhcp4']['option-data']}
        self.assertEqual(len(options), 2)
        self.assertEqual(options['domain-name-servers'], '192.168.123.2')
        self.assertEqual(options['routers'], '192.168.123.1')
        reservations = {r['hw-address']: r['ip-address'] for r in c['Dhcp4']['reservations']}
        self.assertEqual(len(reservations), 2)
        self.assertEqual(reservations['11:22:33:44:aa:a1'], '192.168.123.20')
        self.assertEqual(reservations['11:22:33:44:aa:a2'], '192.168.123.22')
        self.assertEqual(c['Dhcp4']['renew-timer'], 1800,)
        self.assertEqual(c['Dhcp4']['rebind-timer'], 2700,)
        self.assertEqual(c['Dhcp4']['valid-lifetime'], 3600)
        # ipvlan121
        c = json.loads(docker_get_file_content(dcli.containers.get('lpos-ipvlan121-dhcp'), '/etc/kea', 'kea/kea-dhcp4.conf'))
        self.assertEqual(len(c['Dhcp4']['subnet4']), 1)
        self.assertEqual(c['Dhcp4']['subnet4'][0]['subnet'], '172.16.1.0/24')
        self.assertEqual(len(c['Dhcp4']['subnet4'][0]['pools']), 1)
        self.assertEqual(c['Dhcp4']['subnet4'][0]['pools'][0]['pool'], '172.16.1.15-172.16.1.99')
        self.assertEqual(len(c['Dhcp4']['option-data']), 3)
        options = {o['name']: o['data'] for o in c['Dhcp4']['option-data']}
        self.assertEqual(len(options), 3)
        self.assertEqual(options['domain-name-servers'], '172.16.1.12')
        self.assertEqual(options['routers'], '172.16.1.11')
        self.assertEqual(options['v4-captive-portal'], 'http://onboarding.nlpt.network/')
        self.assertEqual(c['Dhcp4']['renew-timer'], 10,)
        self.assertEqual(c['Dhcp4']['rebind-timer'], 20,)
        self.assertEqual(c['Dhcp4']['valid-lifetime'], 30)
        # ipvlan122
        c = json.loads(docker_get_file_content(dcli.containers.get('lpos-ipvlan122-dhcp'), '/etc/kea', 'kea/kea-dhcp4.conf'))
        self.assertEqual(len(c['Dhcp4']['subnet4']), 1)
        self.assertEqual(c['Dhcp4']['subnet4'][0]['subnet'], '172.16.2.0/24')
        self.assertEqual(len(c['Dhcp4']['subnet4'][0]['pools']), 1)
        self.assertEqual(c['Dhcp4']['subnet4'][0]['pools'][0]['pool'], '172.16.2.15-172.16.2.99')
        self.assertEqual(len(c['Dhcp4']['option-data']), 3)
        options = {o['name']: o['data'] for o in c['Dhcp4']['option-data']}
        self.assertEqual(len(options), 3)
        self.assertEqual(options['domain-name-servers'], '172.16.2.12')
        self.assertEqual(options['routers'], '172.16.2.11')
        self.assertEqual(options['v4-captive-portal'], 'http://onboarding.nlpt.network/')
        self.assertEqual(c['Dhcp4']['renew-timer'], 10,)
        self.assertEqual(c['Dhcp4']['rebind-timer'], 20,)
        self.assertEqual(c['Dhcp4']['valid-lifetime'], 30)

    def test_030_dns_docker_container_config(self):
        """
        test dns docker container configuration
        """
        dcli = docker.from_env()
        for i in [113, 112]:
            try:
                dcli.containers.get(f'lpos-ipvlan{i}-dns')
                self.assertTrue(False, f'docker container lpos-ipvlan{i}-dhcp does exist, but shouldnt')
            except docker.errors.NotFound:
                self.assertTrue(True)
        containers = dict({
            121: {
                'name': 'lpos-ipvlan121-dns',
                'network': 'lpos-ipvlan121',
                'ip': '172.16.1.12'
            },
            122: {
                'name': 'lpos-ipvlan122-dns',
                'network': 'lpos-ipvlan122',
                'ip': '172.16.2.12'
            },
        })
        for i in containers.keys():
            try:
                dcon = dcli.containers.get(containers[i]['name'])
            except docker.errors.NotFound:
                self.assertTrue(False, f"docker container {containers[i]['name']} does not exist")
            self.assertEqual(dcon.status, 'running')
            self.assertEqual(dcon.attrs['HostConfig']['NetworkMode'], containers[i]['network'])
            # test mounts
            for m in dcon.attrs['Mounts']:
                if m['Name'] == containers[i]['name']:
                    self.assertEqual(m['Destination'], '/etc/coredns')
                    break
            else:
                self.assertTrue(False, f"could not find required mount in {containers[i]['name']}")
            # test networks
            self.assertEqual(len(dcon.attrs['NetworkSettings']['Networks']), 1)
            self.assertIn(containers[i]['network'], dcon.attrs['NetworkSettings']['Networks'])
            self.assertEqual(dcon.attrs['NetworkSettings']['Networks'][containers[i]['network']]['IPAddress'], containers[i]['ip'])

    def test_045_dns_container_content(self):
        """
        test dns docker container content (configuration)
        """
        dcli = docker.from_env()
        # ipvlan121
        c = docker_get_file_content(dcli.containers.get('lpos-ipvlan121-dns'), '/etc/coredns', 'coredns/Corefile')
        self.assertIn('hosts /etc/coredns/hosts', c)
        c = docker_get_file_content(dcli.containers.get('lpos-ipvlan121-dns'), '/etc/coredns', 'coredns/hosts')
        hosts = {v: k for k, v in [line.split(None, 1) for line in c.strip().split('\n')]}
        self.assertEqual(hosts['onboarding.nlpt.network www.onboarding.nlpt.network'], '172.16.1.11')
        self.assertEqual(hosts['www.msftconnecttest.com'], '172.16.1.11')
        self.assertEqual(hosts['dns.msftncsi.com'], '131.107.255.255')
        self.assertEqual(hosts['nlpt.online'], '172.16.1.14')
        # ipvlan122
        c = docker_get_file_content(dcli.containers.get('lpos-ipvlan122-dns'), '/etc/coredns', 'coredns/Corefile')
        self.assertIn('hosts /etc/coredns/hosts', c)
        c = docker_get_file_content(dcli.containers.get('lpos-ipvlan122-dns'), '/etc/coredns', 'coredns/hosts')
        hosts = {v: k for k, v in [line.split(None, 1) for line in c.strip().split('\n')]}
        self.assertEqual(hosts['onboarding.nlpt.network www.onboarding.nlpt.network'], '172.16.2.11')
        self.assertEqual(hosts['www.msftconnecttest.com'], '172.16.2.11')
        self.assertEqual(hosts['dns.msftncsi.com'], '131.107.255.255')
        self.assertEqual(hosts['nlpt.online'], '172.16.2.14')

    def test_050_haproxy_docker_container_config(self):
        """
        test haproxy docker container configuration
        """
        dcli = docker.from_env()
        # haproxy
        dcon = dcli.containers.list(filters={'name': 'haproxy'})
        self.assertEqual(len(dcon), 1, 'docker container haproxy not found')
        dcon = dcon[0]
        self.assertEqual(dcon.status, 'running')
        self.assertEqual(dcon.attrs['HostConfig']['NetworkMode'], 'bridge')
        self.assertEqual(len(dcon.attrs['Mounts']), 1)
        self.assertEqual(dcon.attrs['Mounts'][0]['Destination'], '/usr/local/etc/haproxy')
        for p in [5555, 80, 8404]:
            self.assertIn(f'{p}/tcp', dcon.attrs['NetworkSettings']['Ports'])
            binds = {e['HostIp']: e['HostPort'] for e in dcon.attrs['NetworkSettings']['Ports'][f'{p}/tcp']}
            self.assertIn('0.0.0.0', binds)
            self.assertEqual(int(binds['0.0.0.0']), p)
        self.assertNotIn('lpos-ipvlan113', dcon.attrs['NetworkSettings']['Networks'])
        self.assertIn('bridge', dcon.attrs['NetworkSettings']['Networks'])
        self.assertIn('lpos-ipvlan112', dcon.attrs['NetworkSettings']['Networks'])
        self.assertEqual(dcon.attrs['NetworkSettings']['Networks']['lpos-ipvlan112']['IPAddress'], '192.168.123.4')
        self.assertIn('lpos-ipvlan121', dcon.attrs['NetworkSettings']['Networks'])
        self.assertEqual(dcon.attrs['NetworkSettings']['Networks']['lpos-ipvlan121']['IPAddress'], '172.16.1.11')
        self.assertIn('lpos-ipvlan122', dcon.attrs['NetworkSettings']['Networks'])
        self.assertEqual(dcon.attrs['NetworkSettings']['Networks']['lpos-ipvlan122']['IPAddress'], '172.16.2.11')
        # ssoproxy
        dcon = dcli.containers.list(filters={'name': 'ssoproxy'})
        self.assertEqual(len(dcon), 1, 'docker container ssoproxy not found')
        dcon = dcon[0]
        self.assertEqual(dcon.status, 'running')
        self.assertEqual(dcon.attrs['HostConfig']['NetworkMode'], 'bridge')
        self.assertEqual(len(dcon.attrs['Mounts']), 1)
        self.assertEqual(dcon.attrs['Mounts'][0]['Destination'], '/usr/local/etc/haproxy')
        self.assertNotIn('lpos-ipvlan112', dcon.attrs['NetworkSettings']['Networks'])
        self.assertNotIn('lpos-ipvlan113', dcon.attrs['NetworkSettings']['Networks'])
        self.assertIn('bridge', dcon.attrs['NetworkSettings']['Networks'])
        self.assertIn('lpos-ipvlan121', dcon.attrs['NetworkSettings']['Networks'])
        self.assertEqual(dcon.attrs['NetworkSettings']['Networks']['lpos-ipvlan121']['IPAddress'], '172.16.1.14')
        self.assertIn('lpos-ipvlan122', dcon.attrs['NetworkSettings']['Networks'])
        self.assertEqual(dcon.attrs['NetworkSettings']['Networks']['lpos-ipvlan122']['IPAddress'], '172.16.2.14')

    def test_055_haproxy_container_content(self):
        """
        test haproxy docker container content (configuration)
        """
        dcli = docker.from_env()
        # haproxy
        c = docker_get_file_content(dcli.containers.list(filters={'name': 'haproxy'})[0], '/usr/local/etc/haproxy', 'haproxy/haproxy.cfg')
        self.assertIn('redirect location http://onboarding.nlpt.network', c)
        # ssoproxy
        c = docker_get_file_content(dcli.containers.list(filters={'name': 'ssoproxy'})[0], '/usr/local/etc/haproxy', 'haproxy/haproxy.cfg')
        self.assertIn('server online_sso 1.2.3.4:80', c)
        self.assertIn('server online_sso 1.2.3.4:443', c)

    def test_100_retreat_everyting(self):
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

    def test_101_no_docker_remains_after_retreat(self):
        """
        after system is retreated no docker elements should exist: container, networks, volumes (starting with lpos-)
        """
        dcli = docker.from_env()
        # TODO: change all compares to 0 after haproxy retreat is implemented
        self.assertEqual(len(dcli.containers.list(filters={'name': 'lpos-'})), 1)
        self.assertEqual(len(dcli.volumes.list(filters={'name': 'lpos-'})), 1)
        self.assertEqual(len(dcli.networks.list(filters={'name': 'lpos-'})), 3)
