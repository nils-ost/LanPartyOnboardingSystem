import unittest
from helpers.docdb import docDB
from elements import Device, Participant, Seat, Table, IpPool, VLAN, Switch
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestDevice(unittest.TestCase):
    def setUp(self):
        docDB.clear()
        # VLANs
        self.v1_id = VLAN({'number': 1, 'purpose': 0}).save().get('created')
        self.v2_id = VLAN({'number': 2, 'purpose': 2}).save().get('created')
        self.v3_id = VLAN({'number': 3, 'purpose': 1}).save().get('created')
        self.v4_id = VLAN({'number': 4, 'purpose': 3}).save().get('created')
        # Switches
        self.sw1_id = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id}).save().get('created')
        # IpPools
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p3_id = IpPool({'range_start': int('C0A80021', 16), 'range_end': int('C0A80030', 16), 'vlan_id': self.v3_id}).save().get('created')
        self.p4_id = IpPool({'range_start': int('C0A80031', 16), 'range_end': int('C0A80040', 16), 'vlan_id': self.v2_id}).save().get('created')
        self.p5_id = IpPool({'range_start': int('C0A80041', 16), 'range_end': int('C0A80050', 16), 'vlan_id': self.v4_id}).save().get('created')
        self.p6_id = IpPool({'range_start': int('C0A80051', 16), 'range_end': int('C0A80060', 16), 'vlan_id': self.v1_id}).save().get('created')
        # Tables
        self.t1_id = Table({'number': 1, 'switch_id': self.sw1_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p2_id}).save().get('created')
        # Seats
        self.s1_id = Seat({'number': 1, 'table_id': self.t1_id}).save().get('created')
        self.s2_id = Seat({'number': 2, 'table_id': self.t1_id}).save().get('created')
        # Participants
        self.pt1_id = Participant({'login': 'part1', 'seat_id': self.s1_id}).save().get('created')
        self.pt2_id = Participant({'login': 'part2', 'seat_id': None}).save().get('created')
        self.pt3_id = Participant({'login': 'part3', 'seat_id': self.s2_id}).save().get('created')

    def test_seat_id_FK_or_None(self):
        self.assertEqual(len(Device.all()), 0)
        # seat_id can be None
        el = Device({'mac': 'mac1', 'seat_id': None})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 1)
        # seat_id can't be a random string
        el = Device({'mac': 'mac2', 'seat_id': 'somerandomstring'})
        self.assertIn('seat_id', el.save()['errors'])
        self.assertEqual(len(Device.all()), 1)
        # but a valid seat_id can be stored
        el = Device({'mac': 'mac2', 'seat_id': self.s1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 2)

    def test_participant_id_FK_or_None(self):
        self.assertEqual(len(Device.all()), 0)
        # participant_id can be None
        el = Device({'mac': 'mac1', 'participant_id': None})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 1)
        # participant_id can't be a random string
        el = Device({'mac': 'mac2', 'participant_id': 'somerandomstring'})
        self.assertIn('participant_id', el.save()['errors'])
        self.assertEqual(len(Device.all()), 1)
        # but a valid participant_id can be stored
        el = Device({'mac': 'mac3', 'participant_id': self.pt1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 2)

    def test_ip_pool_id_FK_or_None(self):
        self.assertEqual(len(Device.all()), 0)
        # ip_pool_id can be None
        el = Device({'mac': 'mac1', 'ip_pool_id': None})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 1)
        # ip_pool_id can't be a random string
        el = Device({'mac': 'mac2', 'ip_pool_id': 'somerandomstring'})
        self.assertIn('ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Device.all()), 1)
        # but a valid ip_pool_id can be stored
        el = Device({'mac': 'mac3', 'ip_pool_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 2)

    def test_seat_id_auto_sets(self):
        # if Seat is set, Participant, IpPool and IP get auto-set based on Seat
        # overwriting those auto-sets is not possible
        self.assertEqual(len(Device.all()), 0)
        # creating a blank Device does not have Participant, IpPool or IP
        el = Device({'mac': 'mac1'})
        self.assertNotIn('errors', el.save())
        self.assertIsNone(el['participant_id'])
        self.assertIsNone(el['ip_pool_id'])
        self.assertIsNone(el['ip'])
        # now assigning a Seat to the Device sets Participant, IpPool and IP
        el['seat_id'] = self.s2_id
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['participant_id'], self.pt3_id)
        self.assertEqual(el['ip_pool_id'], self.p1_id)
        self.assertEqual(el['ip'], int('C0A80002', 16))
        # overwriting Participant, IpPool and IP doesn't have any effect
        el['participant_id'] = self.pt2_id
        el['ip_pool_id'] = self.p2_id
        el['ip'] = int('C0A80012', 16)
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['participant_id'], self.pt3_id)
        self.assertEqual(el['ip_pool_id'], self.p1_id)
        self.assertEqual(el['ip'], int('C0A80002', 16))
        # directly creating Device with Seat also sets Participant, IpPool and IP
        el = Device({'mac': 'mac2', 'seat_id': self.s1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['participant_id'], self.pt1_id)
        self.assertEqual(el['ip_pool_id'], self.p1_id)
        self.assertEqual(el['ip'], int('C0A80001', 16))

    def test_participant_id_auto_sets(self):
        # if Participant is set, IpPool and IP get auto-set based on Participant's Tables's add_IpPool
        # but IpPool and IP can be overwritten
        self.assertEqual(len(Device.all()), 0)
        # creating a blank Device does not have IpPool or IP
        el = Device({'mac': 'mac1'})
        self.assertNotIn('errors', el.save())
        self.assertIsNone(el['ip_pool_id'])
        self.assertIsNone(el['ip'])
        # now assigning a Participant to the Device sets IpPool and IP
        el['participant_id'] = self.pt1_id
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['ip_pool_id'], self.p2_id)
        self.assertEqual(el['ip'], int('C0A80011', 16))
        # overwriting IP is possible
        el['ip'] = int('C0A80013', 16)
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['ip'], int('C0A80013', 16))
        # overwriting IpPool is also possible
        el['ip_pool_id'] = self.p6_id
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['ip_pool_id'], self.p6_id)
        self.assertEqual(el['ip'], int('C0A80051', 16))
        # but IpPool can't be a seat_IpPool
        el['ip_pool_id'] = self.p1_id
        self.assertIn('ip_pool_id', el.save()['errors'])
        # creating a Device with Participant, that does not have a Seat does not set IpPool or IP
        el = Device({'mac': 'mac2', 'participant_id': self.pt2_id})
        self.assertNotIn('errors', el.save())
        self.assertIsNone(el['ip_pool_id'])
        self.assertIsNone(el['ip'])

    def test_ip_pool_id_auto_sets(self):
        # if IpPool is set, IP gets first available IP in IpPool
        # IP can be overwritten
        self.assertEqual(len(Device.all()), 0)
        # creating a blank Device does not have a IP
        el = Device({'mac': 'mac1'})
        self.assertNotIn('errors', el.save())
        self.assertIsNone(el['ip'])
        # now assigning a IpPool to the Device sets IP
        el['ip_pool_id'] = self.p6_id
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['ip'], int('C0A80051', 16))
        # overwriting the IP is possible
        el['ip'] = int('C0A80055', 16)
        self.assertNotIn('errors', el.save())
        self.assertEqual(el['ip'], int('C0A80055', 16))
        # but a IpPool can't be a set_IpPool
        el['ip_pool_id'] = self.p1_id
        self.assertIn('ip_pool_id', el.save()['errors'])

    def test_ip_requires_ip_pool_id_and_range(self):
        # IP can only be set if IpPool is set
        # and IP needs to fall into IpPool
        self.assertEqual(len(Device.all()), 0)
        # assign IP without IpPool is not allowed
        el = Device({'mac': 'mac1', 'ip': int('C0A80005', 16)})
        self.assertIn('ip', el.save()['errors'])
        self.assertEqual(len(Device.all()), 0)
        # but with a matching IpPool it's fine
        el = Device({'mac': 'mac2', 'ip_pool_id': self.p1_id, 'ip': int('C0A80005', 16)})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 1)
        el.reload()
        self.assertEqual(el['ip'], int('C0A80005', 16))  # IP still as set, after save and reload from DB
        # first IP of IpPool is fine to be used
        el = Device({'mac': 'mac3', 'ip_pool_id': self.p1_id, 'ip': int('C0A80001', 16)})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 2)
        # last IP of IpPool is fine to be used
        el = Device({'mac': 'mac4', 'ip_pool_id': self.p1_id, 'ip': int('C0A80010', 16)})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 3)
        # one IP in front of IpPool is not allowed
        el = Device({'mac': 'mac5', 'ip_pool_id': self.p1_id, 'ip': int('C0A80000', 16)})
        self.assertIn('ip', el.save()['errors'])
        self.assertEqual(len(Device.all()), 3)
        # one IP after IpPool is not allowed
        el = Device({'mac': 'mac6', 'ip_pool_id': self.p1_id, 'ip': int('C0A80011', 16)})
        self.assertIn('ip', el.save()['errors'])
        self.assertEqual(len(Device.all()), 3)

    def test_ip_pool_id_vlan_purpose(self):
        # if Participant is set the pupose of IpPool's VLAN needs to be 0 (play)
        # otherwise IpPool's VLAN purpose can by anything
        self.assertEqual(len(Device.all()), 0)
        # with Participant IpPools VLAN 0 is allowed
        el = Device({'mac': 'mac1', 'participant_id': self.pt1_id, 'ip_pool_id': self.p2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 1)
        # with Participant IpPools VLAN 1 is not allowed
        el = Device({'mac': 'mac2', 'participant_id': self.pt1_id, 'ip_pool_id': self.p3_id})
        self.assertIn('ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Device.all()), 1)
        # with Participant IpPools VLAN 2 is not allowed
        el = Device({'mac': 'mac3', 'participant_id': self.pt1_id, 'ip_pool_id': self.p4_id})
        self.assertIn('ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Device.all()), 1)
        # with Participant IpPools VLAN 3 is not allowed
        el = Device({'mac': 'mac4', 'participant_id': self.pt1_id, 'ip_pool_id': self.p5_id})
        self.assertIn('ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Device.all()), 1)
        # without Participant IpPools VLAN 0 is allowed
        el = Device({'mac': 'mac5', 'ip_pool_id': self.p2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 2)
        # without Participant IpPools VLAN 1 is allowed
        el = Device({'mac': 'mac6', 'ip_pool_id': self.p3_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 3)
        # without Participant IpPools VLAN 2 is allowed
        el = Device({'mac': 'mac7', 'ip_pool_id': self.p4_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 4)
        # without Participant IpPools VLAN 3 is allowed
        el = Device({'mac': 'mac8', 'ip_pool_id': self.p5_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Device.all()), 5)


setup_module = setUpModule
teardown_module = tearDownModule


class TestDeviceApi(ApiTestBase):
    _element = Device
    _path = 'device'
    _patch_valid = {'desc': 'Hello World'}
    _patch_invalid = {'desc': None}

    def setUp(self):
        docDB.clear()
        self._setup_el1 = {'mac': 'mac1'}
        self._setup_el2 = {'mac': 'mac2'}
        self._post_valid = {'mac': 'mac3'}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
