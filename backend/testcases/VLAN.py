import unittest
from helpers.docdb import docDB
from elements import VLAN
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestVLAN(unittest.TestCase):
    def setUp(self):
        docDB.clear()

    def test_number_int_and_notnone(self):
        self.assertEqual(len(VLAN.all()), 0)
        # if number is None it can't be saved
        el1 = VLAN({'number': None})
        result = el1.save()
        self.assertIn('not to be None', result['errors']['number'])
        self.assertEqual(len(VLAN.all()), 0)
        # if number is not int it can't be saved
        el1['number'] = 'somerandomstring'
        result = el1.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 0)
        # if number is lower than 1 it can't be saved
        el1['number'] = 0
        result = el1.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 0)
        # if number is bigger than 1024 it can't be saved
        el1['number'] = 1025
        result = el1.save()
        self.assertIn('number', result['errors'])
        self.assertEqual(len(VLAN.all()), 0)
        # now with valid number it is possible to save
        el1['number'] = 1
        result = el1.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(VLAN.all()), 1)


setup_module = setUpModule
teardown_module = tearDownModule


class TestVLANApi(ApiTestBase):
    _element = VLAN
    _path = 'vlan'
    _patch_valid = {'purpose': 2}
    _patch_invalid = {'purpose': -1}

    def setUp(self):
        docDB.clear()
        self._setup_el1 = {'number': 1}
        self._setup_el2 = {'number': 2}
        self._post_valid = {'number': 3}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
