import unittest
from noapiframe import docDB
from elements import Table, IpPool, VLAN, Switch
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestTable(unittest.TestCase):
    def setUp(self):
        docDB.clear()
        # VLANs
        self.v1_id = VLAN({'number': 1, 'purpose': 0}).save().get('created')
        self.v2_id = VLAN({'number': 2, 'purpose': 2}).save().get('created')
        self.v3_id = VLAN({'number': 3, 'purpose': 2}).save().get('created')
        self.v4_id = VLAN({'number': 4, 'purpose': 1}).save().get('created')
        self.v5_id = VLAN({'number': 5, 'purpose': 3}).save().get('created')
        # Switches
        s1 = Switch({'addr': 'sw1', 'purpose': 0})
        self.s1_id = s1.save().get('created')
        s2 = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id})
        self.s2_id = s2.save().get('created')
        s3 = Switch({'addr': 'sw3', 'purpose': 2, 'onboarding_vlan_id': self.v3_id})
        self.s3_id = s3.save().get('created')
        # IpPools
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p3_id = IpPool({'range_start': int('C0A80021', 16), 'range_end': int('C0A80030', 16), 'vlan_id': self.v2_id}).save().get('created')
        self.p4_id = IpPool({'range_start': int('C0A80031', 16), 'range_end': int('C0A80040', 16), 'vlan_id': self.v4_id}).save().get('created')
        self.p5_id = IpPool({'range_start': int('C0A80041', 16), 'range_end': int('C0A80050', 16), 'vlan_id': self.v5_id}).save().get('created')
        self.p6_id = IpPool({'range_start': int('C0A80051', 16), 'range_end': int('C0A80060', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p7_id = IpPool({'range_start': int('C0A80061', 16), 'range_end': int('C0A80070', 16), 'vlan_id': self.v1_id}).save().get('created')

    def test_number_range(self):
        # number needs to be positive or zero
        self.assertEqual(len(Table.all()), 0)
        # negative number is not possible
        el = Table({'number': -1, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': self.s2_id})
        self.assertIn('number', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # zero is possible
        el = Table({'number': 0, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': self.s2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)
        # positive is possible
        el = Table({'number': 1, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p2_id, 'switch_id': self.s2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 2)

    def test_switch_id_FK_and_notnone(self):
        self.assertEqual(len(Table.all()), 0)
        # switch_id can't be None
        el = Table({'number': 1, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': None})
        self.assertIn('switch_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # switch_id can't be a random string
        el = Table({'number': 1, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': 'somerandomstring'})
        self.assertIn('switch_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # but a valid switch_id can be stored
        el = Table({'number': 1, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': self.s2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)

    def test_switch_purpose(self):
        # The purpose of Switch needs to be 1 or 2
        self.assertEqual(len(Table.all()), 0)
        # switch with purpose 0 is not allowed
        el = Table({'number': 1, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': self.s1_id})
        self.assertIn('switch_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # switch with purpose 1 is allowed
        el = Table({'number': 2, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p1_id, 'switch_id': self.s2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)
        # switch with purpose 2 is allowed
        el = Table({'number': 3, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p2_id, 'switch_id': self.s3_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 2)

    def test_seat_ip_pool_id_FK_and_notnone(self):
        self.assertEqual(len(Table.all()), 0)
        # seat_ip_pool_id can't be None
        el = Table({'number': 1, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': None})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # seat_ip_pool_id can't be a random string
        el = Table({'number': 1, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': 'somerandomstring'})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # but a valid seat_ip_pool_id can be stored
        el = Table({'number': 1, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)

    def test_seat_ip_pool_id_unique(self):
        # a IpPool is only allowed to be associated with one table
        self.assertEqual(len(Table.all()), 0)
        # a IpPool can be assigned to a Table
        el = Table({'number': 1, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)
        # but not to another table
        el = Table({'number': 2, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p1_id})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 1)
        # a second IpPool can again assigned to a Table
        el = Table({'number': 2, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p6_id, 'seat_ip_pool_id': self.p2_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Table.all()), 2)
        # editing this Table is no problem
        el['number'] = 3
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Table.all()), 2)
        # IpPool can't be used if is used as add_ip_pool_id allready
        el = Table({'number': 4, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p7_id, 'seat_ip_pool_id': self.p6_id})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 2)

    def test_seat_ip_pool_ids_vlan_purpose(self):
        # The VLAN of seat_ip_pool needs to be of purpose 0 (play/seats)
        self.assertEqual(len(Table.all()), 0)
        # using an IpPool with VLAN purpose 1 is not possible
        el = Table({'number': 1, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p4_id})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # using an IpPool with VLAN purpose 2 is not possible
        el = Table({'number': 2, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p3_id})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # using an IpPool with VLAN purpose 3 is not possible
        el = Table({'number': 3, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p5_id})
        self.assertIn('seat_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # but using an IpPool with VLAN purpose 0 is possible
        el = Table({'number': 4, 'switch_id': self.s2_id, 'add_ip_pool_id': self.p2_id, 'seat_ip_pool_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)

    def test_add_ip_pool_id_FK_and_notnone(self):
        self.assertEqual(len(Table.all()), 0)
        # add_ip_pool_id can't be None
        el = Table({'number': 1, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': None})
        self.assertIn('add_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # add_ip_pool_id can't be a random string
        el = Table({'number': 1, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': 'somerandomstring'})
        self.assertIn('add_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # but a valid add_ip_pool_id can be stored
        el = Table({'number': 1, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)

    def test_add_ip_pool_ids_vlan_purpose(self):
        # The VLAN of add_ip_pool needs to be of purpose 0 (play/seats)
        self.assertEqual(len(Table.all()), 0)
        # using an IpPool with VLAN purpose 1 is not possible
        el = Table({'number': 1, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p4_id})
        self.assertIn('add_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # using an IpPool with VLAN purpose 2 is not possible
        el = Table({'number': 2, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p3_id})
        self.assertIn('add_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # using an IpPool with VLAN purpose 3 is not possible
        el = Table({'number': 3, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p5_id})
        self.assertIn('add_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 0)
        # but using an IpPool with VLAN purpose 0 is possible
        el = Table({'number': 4, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)

    def test_add_ip_pool_id_not_used_on_seats(self):
        self.assertEqual(len(Table.all()), 0)
        # create a reference Table
        el = Table({'number': 1, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 1)
        # p1_id allready used as seat_ip_pool_id, so it can't be used as add_ip_pool_id
        el = Table({'number': 2, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p6_id, 'add_ip_pool_id': self.p1_id})
        self.assertIn('add_ip_pool_id', el.save()['errors'])
        self.assertEqual(len(Table.all()), 1)
        # but using the same add_ip_pool_id multiple times is fine
        el = Table({'number': 2, 'switch_id': self.s2_id, 'seat_ip_pool_id': self.p6_id, 'add_ip_pool_id': self.p2_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Table.all()), 2)


setup_module = setUpModule
teardown_module = tearDownModule


class TestTableApi(ApiTestBase):
    _element = Table
    _path = 'table'
    _patch_valid = {'desc': 'hi'}
    _patch_invalid = {'desc': None}
    _restricted_read = True
    _restricted_write = True

    def setUp(self):
        docDB.clear()
        self.v1_id = VLAN({'number': 1, 'purpose': 0}).save().get('created')
        self.v2_id = VLAN({'number': 2, 'purpose': 2}).save().get('created')
        self.s1_id = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': self.v2_id}).save().get('created')
        self.p1_id = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80010', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p2_id = IpPool({'range_start': int('C0A80011', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p3_id = IpPool({'range_start': int('C0A80021', 16), 'range_end': int('C0A80030', 16), 'vlan_id': self.v1_id}).save().get('created')
        self.p4_id = IpPool({'range_start': int('C0A80031', 16), 'range_end': int('C0A80040', 16), 'vlan_id': self.v1_id}).save().get('created')
        self._setup_el1 = {'number': 1, 'switch_id': self.s1_id, 'seat_ip_pool_id': self.p1_id, 'add_ip_pool_id': self.p4_id}
        self._setup_el2 = {'number': 2, 'switch_id': self.s1_id, 'seat_ip_pool_id': self.p2_id, 'add_ip_pool_id': self.p4_id}
        self._post_valid = {'number': 3, 'switch_id': self.s1_id, 'seat_ip_pool_id': self.p3_id, 'add_ip_pool_id': self.p4_id}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
