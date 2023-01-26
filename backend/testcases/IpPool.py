import unittest
from helpers.docdb import docDB
from elements import IpPool, VLAN
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestIpPool(unittest.TestCase):
    def setUp(self):
        docDB.clear()
        v1 = VLAN({'number': 1})
        self.v1_id = v1.save().get('created')

    def test_range_of_purpose(self):
        self.assertEqual(len(IpPool.all()), 0)
        # if purpose is lower than 0 it can't be saved
        el = IpPool({'purpose': -1, 'range_start': int('0CA80002', 16), 'range_end': int('0CA80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but 0 works
        el = IpPool({'purpose': 0, 'range_start': int('0CA80002', 16), 'range_end': int('0CA80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)
        # if purpose is bigger than 3 it can't be saved
        el = IpPool({'purpose': 4, 'range_start': int('C0A80002', 16), 'range_end': int('C0A80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # but 3 works
        el = IpPool({'purpose': 3, 'range_start': int('C0A80002', 16), 'range_end': int('C0A80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 2)

    def test_range_of_mask(self):
        self.assertEqual(len(IpPool.all()), 0)
        # if mask is lower than 8 it can't be saved
        el = IpPool({'mask': 7, 'range_start': int('0CA80002', 16), 'range_end': int('0CA80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('mask', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but 8 works
        el = IpPool({'mask': 8, 'range_start': int('0CA80002', 16), 'range_end': int('0CA80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)
        # if mask is bigger than 30 it can't be saved
        el = IpPool({'mask': 31, 'range_start': int('C0A80001', 16), 'range_end': int('C0A80002', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('mask', result['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # but 30 works
        el = IpPool({'mask': 30, 'range_start': int('C0A80001', 16), 'range_end': int('C0A80002', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 2)

    def test_range_of_range_start(self):
        self.assertEqual(len(IpPool.all()), 0)
        # range_start can't be smaller than 0x01000000
        el = IpPool({'range_start': int('00FFFFFF', 16), 'range_end': int('01000001', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_start', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but 0x01000000 is ok
        el = IpPool({'range_start': int('01000000', 16), 'range_end': int('01000001', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)
        # remove all IpPools otherwise we would get a overlapping error in the next steps
        docDB.clear('IpPool')
        self.assertEqual(len(IpPool.all()), 0)
        # range_start can't be bigger than 0xFFFFFFFD
        el = IpPool({'range_start': int('FFFFFFFE', 16), 'range_end': int('FFFFFFFF', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_start', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but 0xFFFFFD is ok
        el = IpPool({'range_start': int('FFFFFFFD', 16), 'range_end': int('FFFFFFFE', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)

    def test_range_of_range_end(self):
        self.assertEqual(len(IpPool.all()), 0)
        # range_end can't be smaller than 0x01000001
        el = IpPool({'range_start': int('00FFFFFF', 16), 'range_end': int('01000000', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_end', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but 0x01000001 is ok
        el = IpPool({'range_start': int('01000000', 16), 'range_end': int('01000001', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)
        # remove all IpPools otherwise we would get a overlapping error in the next steps
        docDB.clear('IpPool')
        self.assertEqual(len(IpPool.all()), 0)
        # range_end can't be bigger than 0xFFFFFFFE
        el = IpPool({'range_start': int('FFFFFFFD', 16), 'range_end': int('FFFFFFFF', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_end', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but 0xFFFFFE is ok
        el = IpPool({'range_start': int('FFFFFFFD', 16), 'range_end': int('FFFFFFFE', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)

    def test_vlan_id_FK_and_notnone(self):
        self.assertEqual(len(IpPool.all()), 0)
        # vlan_id can't be None
        el = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80020', 16), 'vlan_id': None})
        self.assertIn('vlan_id', el.save()['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # vlan_id can't be a random string
        el = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80020', 16), 'vlan_id': 'somerandomstring'})
        self.assertIn('vlan_id', el.save()['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but a valid vlan_id can be stored
        el = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(IpPool.all()), 1)

    def test_mask_compatible_with_range(self):
        # the range C0A80001 to C0A801FF does not fall onto the mask 24
        el = IpPool({'mask': 24, 'range_start': int('C0A80001', 16), 'range_end': int('C0A801FF', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('mask', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # but with a mask of 23 this range would be ok
        el = IpPool({'mask': 23, 'range_start': int('C0A80001', 16), 'range_end': int('C0A801FF', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)
        # remove all IpPools otherwise we would get a overlapping error in the next steps
        docDB.clear('IpPool')
        self.assertEqual(len(IpPool.all()), 0)
        # also changing the range to C0A80101 to C0A801FF makes it compatible with the mask 24
        el = IpPool({'mask': 24, 'range_start': int('C0A80101', 16), 'range_end': int('C0A801FF', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)

    def test_range_overlapping_other_ippool(self):
        self.assertEqual(len(IpPool.all()), 0)
        # create reference IpPool C0A8001E to C0A80032
        el = IpPool({'range_start': int('C0A8001E', 16), 'range_end': int('C0A80032', 16), 'vlan_id': self.v1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(IpPool.all()), 1)
        # new pool overlapps in the start of ref pool, error
        el = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A80020', 16), 'vlan_id': self.v1_id})
        self.assertIn('range_end', el.save()['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # new pool hits start of ref pool, error
        el = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A8001E', 16), 'vlan_id': self.v1_id})
        self.assertIn('range_end', el.save()['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # new pool overlapps in the end of ref pool, error
        el = IpPool({'range_start': int('C0A80030', 16), 'range_end': int('C0A80046', 16), 'vlan_id': self.v1_id})
        self.assertIn('range_start', el.save()['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # new pool hits end of ref pool, error
        el = IpPool({'range_start': int('C0A80032', 16), 'range_end': int('C0A80046', 16), 'vlan_id': self.v1_id})
        self.assertIn('range_start', el.save()['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # new pool fully submerged in ref pool, error
        el = IpPool({'range_start': int('C0A80023', 16), 'range_end': int('C0A8002D', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_start', result['errors'])
        self.assertIn('range_end', result['errors'])
        self.assertEqual(len(IpPool.all()), 1)
        # new pool exactly in front of ref pool, thats ok
        el = IpPool({'range_start': int('C0A80001', 16), 'range_end': int('C0A8001D', 16), 'vlan_id': self.v1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(IpPool.all()), 2)
        # new pool exactly after ref pool, thats ok
        el = IpPool({'range_start': int('C0A80033', 16), 'range_end': int('C0A80046', 16), 'vlan_id': self.v1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(IpPool.all()), 3)

    def test_valid_range(self):
        # range_start < range_end
        self.assertEqual(len(IpPool.all()), 0)
        # range start and end can't be equal
        el = IpPool({'range_start': int('C0A80009', 16), 'range_end': int('C0A80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_start', result['errors'])
        self.assertIn('range_end', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # range end can't be lower than range start
        el = IpPool({'range_start': int('C0A80009', 16), 'range_end': int('C0A80008', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertIn('range_start', result['errors'])
        self.assertIn('range_end', result['errors'])
        self.assertEqual(len(IpPool.all()), 0)
        # range end bigger than range start is valid
        el = IpPool({'range_start': int('C0A80008', 16), 'range_end': int('C0A80009', 16), 'vlan_id': self.v1_id})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(IpPool.all()), 1)


setup_module = setUpModule
teardown_module = tearDownModule


class TestIpPoolApi(ApiTestBase):
    _element = IpPool
    _path = 'ippool'
    _patch_valid = {'purpose': 3}
    _patch_invalid = {'purpose': -1}

    def setUp(self):
        docDB.clear()
        v1 = VLAN({'number': 1})
        self.v1_id = v1.save().get('created')
        self._setup_el1 = {'range_start': int('C0A80023', 16), 'range_end': int('C0A8002D', 16), 'vlan_id': self.v1_id}
        self._setup_el2 = {'range_start': int('C0A80033', 16), 'range_end': int('C0A8003D', 16), 'vlan_id': self.v1_id}
        self._post_valid = {'range_start': int('C0A80043', 16), 'range_end': int('C0A8004D', 16), 'vlan_id': self.v1_id}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
