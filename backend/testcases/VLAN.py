import unittest
from noapiframe import docDB
from elements import VLAN
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestVLAN(unittest.TestCase):
    def setUp(self):
        docDB.clear()

    def test_range_of_number(self):
        self.assertEqual(len(VLAN.all()), 0)
        # if number is lower than 1 it can't be saved
        el1 = VLAN({'number': 0})
        result = el1.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 0)
        # but 1 works
        el1['number'] = 1
        result = el1.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 1)
        # if number is bigger than 1024 it can't be saved
        el2 = VLAN({'number': 1025})
        result = el2.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 1)
        # but 1024 work
        el2['number'] = 1024
        result = el2.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 2)

    def test_number_uniqueness(self):
        self.assertEqual(len(VLAN.all()), 0)
        # if number can't be None
        el1 = VLAN({'number': None})
        result = el1.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 0)
        # but a not used number
        el1['number'] = 1
        result = el1.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 1)
        # a used number can't be used again
        el2 = VLAN({'number': 1})
        result = el2.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 1)
        # but another unused number is ok
        el2['number'] = 2
        result = el2.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 2)

    def test_range_of_purpose(self):
        self.assertEqual(len(VLAN.all()), 0)
        # if purpose is lower than 0 it can't be saved
        el1 = VLAN({'purpose': -1, 'number': 1})
        result = el1.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(VLAN.all()), 0)
        # but 0 works
        el1['purpose'] = 0
        result = el1.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 1)
        # if purpose is bigger than 3 it can't be saved
        el2 = VLAN({'purpose': 4, 'number': 2})
        result = el2.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(VLAN.all()), 1)
        # but 3 works
        el2['purpose'] = 3
        result = el2.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 2)

    def test_purpose_uniqueness(self):
        # purpose 0 (play) and 1 (mgmt) can only be used once
        self.assertEqual(len(VLAN.all()), 0)
        # create one with purpose 0 is fine
        el = VLAN({'purpose': 0, 'number': 1})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 1)
        # create another with purpose 0 is not ok
        el = VLAN({'purpose': 0, 'number': 2})
        result = el.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(VLAN.all()), 1)
        # create one with purpose 1 is fine
        el = VLAN({'purpose': 1, 'number': 3})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 2)
        # create another with purpose 1 is not ok
        el = VLAN({'purpose': 1, 'number': 4})
        result = el.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(VLAN.all()), 2)
        # create one with purpose 2 is fine
        el = VLAN({'purpose': 2, 'number': 5})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 3)
        # create another with purpose 2 is fine too
        el = VLAN({'purpose': 2, 'number': 6})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 4)
        # create one with purpose 3 is fine
        el = VLAN({'purpose': 3, 'number': 7})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 5)
        # create another with purpose 3 is fine too
        el = VLAN({'purpose': 3, 'number': 8})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 6)


setup_module = setUpModule
teardown_module = tearDownModule


class TestVLANApi(ApiTestBase):
    _element = VLAN
    _path = 'vlan'
    _patch_valid = {'purpose': 2}
    _patch_invalid = {'purpose': -1}
    _restricted_read = True
    _restricted_write = True

    def setUp(self):
        docDB.clear()
        self._setup_el1 = {'number': 1}
        self._setup_el2 = {'number': 2}
        self._post_valid = {'number': 3}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
