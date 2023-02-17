import unittest
from helpers.docdb import docDB
from elements import Seat, Table, IpPool, VLAN, Switch
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestSeat(unittest.TestCase):
    def setUp(self):
        docDB.clear()
        # VLANs
        self.v1_id = VLAN({'number': 1, 'purpose': 0}).save().get('created')
        self.v2_id = VLAN({'number': 2, 'purpose': 2}).save().get('created')
        # Switches
        self.s1_id = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id}).save().get('created')
        # IpPools
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p3_id = IpPool({'range_start': int('C0A80021', 16), 'range_end': int('C0A80030', 16), 'vlan_id': self.v1_id}).save().get('created')
        # Tables
        self.t1_id = Table({'number': 1, 'switch_id': self.s1_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p3_id}).save().get('created')
        self.t2_id = Table({'number': 2, 'switch_id': self.s1_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p3_id}).save().get('created')

    def test_table_id_FK_and_notnone(self):
        self.assertEqual(len(Seat.all()), 0)
        # table_id can't be None
        el = Seat({'number': 1, 'table_id': None})
        self.assertIn('table_id', el.save()['errors'])
        self.assertEqual(len(Seat.all()), 0)
        # table_id can't be a random string
        el = Seat({'number': 1, 'table_id': 'somerandomstring'})
        self.assertIn('table_id', el.save()['errors'])
        self.assertEqual(len(Seat.all()), 0)
        # but a valid table_id can be stored
        el = Seat({'number': 1, 'table_id': self.t1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Seat.all()), 1)

    def test_number_unique_per_table(self):
        self.assertEqual(len(Seat.all()), 0)
        # number 1 can be on table 1
        el = Seat({'number': 1, 'table_id': self.t1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Seat.all()), 1)
        # number 2 can be on table 1
        el = Seat({'number': 2, 'table_id': self.t1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Seat.all()), 2)
        # number 1 can't be on table 1 again
        el = Seat({'number': 1, 'table_id': self.t1_id})
        self.assertIn('number', el.save()['errors'])
        self.assertEqual(len(Seat.all()), 2)
        # but number 1 can be on table 2
        el = Seat({'number': 1, 'table_id': self.t2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Seat.all()), 3)

    def test_number_range(self):
        # needs to be positive and not 0
        self.assertEqual(len(Seat.all()), 0)
        # negative is not allowed
        el = Seat({'number': -1, 'table_id': self.t1_id})
        self.assertIn('number', el.save()['errors'])
        self.assertEqual(len(Seat.all()), 0)
        # zero is not allowed
        el = Seat({'number': 0, 'table_id': self.t1_id})
        self.assertIn('number', el.save()['errors'])
        self.assertEqual(len(Seat.all()), 0)
        # one is allowed
        el = Seat({'number': 1, 'table_id': self.t1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Seat.all()), 1)


setup_module = setUpModule
teardown_module = tearDownModule


class TestSeatApi(ApiTestBase):
    _element = Seat
    _path = 'seat'
    _patch_valid = {'number': 4}
    _patch_invalid = {'number': -1}
    _restricted_read = True
    _restricted_write = True

    def setUp(self):
        docDB.clear()
        self.v1_id = VLAN({'number': 1, 'purpose': 0}).save().get('created')
        self.v2_id = VLAN({'number': 2, 'purpose': 2}).save().get('created')
        self.s1_id = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id}).save().get('created')
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.t1_id = Table({'number': 1, 'switch_id': self.s1_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p2_id}).save().get('created')
        self._setup_el1 = {'number': 1, 'table_id': self.t1_id}
        self._setup_el2 = {'number': 2, 'table_id': self.t1_id}
        self._post_valid = {'number': 3, 'table_id': self.t1_id}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
