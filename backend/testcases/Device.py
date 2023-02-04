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
        # Switches
        self.sw1_id = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id}).save().get('created')
        # IpPools
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        # Tables
        self.t1_id = Table({'number': 1, 'switch_id': self.sw1_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p2_id}).save().get('created')
        # Seats
        self.s1_id = Seat({'number': 1, 'table_id': self.t1_id}).save().get('created')
        self.s2_id = Seat({'number': 2, 'table_id': self.t1_id}).save().get('created')

    def test_seat_id_FK_or_None(self):
        self.assertTrue(False)
        self.assertEqual(len(Device.all()), 0)

    def test_participant_id_FK_or_None(self):
        self.assertTrue(False)

    def test_ip_pool_id_FK_or_None(self):
        self.assertTrue(False)

    def test_seat_id_auto_sets(self):
        # if Seat is set, Participant, IpPool and IP get auto-set based on Seat
        # overwriting those auto-sets is not possible
        self.assertTrue(False)

    def test_participant_id_auto_sets(self):
        # if Participant is set, IpPool and IP get auto-set based on Participant's Tables's add_IpPool
        # but IpPool and IP can be overwritten
        self.assertTrue(False)

    def test_ip_pool_id_auto_sets(self):
        # if IpPool is set, IP gets first available IP in IpPool
        # IP can be overwritten
        self.assertTrue(False)

    def test_ip_requires_ip_pool_id_and_range(self):
        # IP can only be set if IpPool is set
        # and IP needs to fall into IpPool
        self.assertTrue(False)

    def test_ip_pool_id_vlan_purpose(self):
        # if Participant is set the pupose of IpPool's VLAN needs to be 0 (play)
        # otherwise IpPool's VLAN purpose can by anything
        self.assertTrue(False)


setup_module = setUpModule
teardown_module = tearDownModule


class TestParticipantApi(ApiTestBase):
    _element = Participant
    _path = 'participant'
    _patch_valid = {'admin': True}
    _patch_invalid = {'name': None}

    def setUp(self):
        docDB.clear()
        self.v1_id = VLAN({'number': 1, 'purpose': 0}).save().get('created')
        self.v2_id = VLAN({'number': 2, 'purpose': 2}).save().get('created')
        self.sw1_id = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id}).save().get('created')
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.t1_id = Table({'number': 1, 'switch_id': self.sw1_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p1_id}).save().get('created')
        self.s1_id = Seat({'number': 1, 'table_id': self.t1_id}).save().get('created')
        self.s2_id = Seat({'number': 2, 'table_id': self.t1_id}).save().get('created')
        self._setup_el1 = {'seat_id': self.s1_id}
        self._setup_el2 = {'seat_id': self.s2_id}
        self._post_valid = {'name': 'Hello World'}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
