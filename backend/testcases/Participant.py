import unittest
from noapiframe import docDB
from elements import Participant, Seat, Table, IpPool, VLAN, Switch
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestParticipant(unittest.TestCase):
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

    def test_login_unique_or_None(self):
        self.assertEqual(len(Participant.all()), 0)
        # login can be None
        el = Participant({'login': None})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 1)
        # login can be random string
        el = Participant({'login': 'somerandomstring'})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 2)
        # login can't be used again
        el = Participant({'login': 'somerandomstring'})
        self.assertIn('login', el.save()['errors'])
        self.assertEqual(len(Participant.all()), 2)
        # but a different string is no problem
        el = Participant({'login': 'somerandomstring2'})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 3)

    def test_seat_id_FK_or_None(self):
        self.assertEqual(len(Participant.all()), 0)
        # seat_id can be None
        el = Participant({'seat_id': None})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 1)
        # seat_id can't be a random string
        el = Participant({'seat_id': 'somerandomstring'})
        self.assertIn('seat_id', el.save()['errors'])
        self.assertEqual(len(Participant.all()), 1)
        # but a valid seat_id can be stored
        el = Participant({'seat_id': self.s1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 2)

    def test_seat_id_unique(self):
        self.assertEqual(len(Participant.all()), 0)
        # seat_id can be used once
        el = Participant({'seat_id': self.s1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 1)
        # but not twice
        el = Participant({'seat_id': self.s1_id})
        self.assertIn('seat_id', el.save()['errors'])
        self.assertEqual(len(Participant.all()), 1)
        # a different seat_id is fine
        el = Participant({'seat_id': self.s2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Participant.all()), 2)
        # but just once again
        el = Participant({'seat_id': self.s2_id})
        self.assertIn('seat_id', el.save()['errors'])
        self.assertEqual(len(Participant.all()), 2)


setup_module = setUpModule
teardown_module = tearDownModule


class TestParticipantApi(ApiTestBase):
    _element = Participant
    _path = 'participant'
    _patch_valid = {'admin': True}
    _patch_invalid = {'name': None}
    _restricted_read = True
    _restricted_write = True

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
