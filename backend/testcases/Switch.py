import unittest
from helpers.docdb import docDB
from elements import VLAN, Switch
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestSwitch(unittest.TestCase):
    def setUp(self):
        docDB.clear()

    def test_range_of_purpose(self):
        self.assertEqual(len(Switch.all()), 0)
        # if purpose is lower than 0 it can't be saved
        el1 = Switch({'addr': 'sw1', 'purpose': -1})
        result = el1.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # but 0 works
        el1['purpose'] = 0
        result = el1.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)
        # if purpose is bigger than 2 it can't be saved
        el2 = Switch({'addr': 'sw2', 'purpose': 3})
        result = el2.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(Switch.all()), 1)
        # but 2 work
        el2['purpose'] = 2
        result = el2.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 2)

    def test_participant_vlan_id_FK_or_None(self):
        self.assertEqual(len(Switch.all()), 0)
        # if participant_vlan_id is None, this is ok
        el = Switch({'addr': 'sw1', 'participant_vlan_id': None})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)
        # if participant_vlan_id is a random string, this is not ok
        el = Switch({'addr': 'sw2', 'participant_vlan_id': 'somerandomstring'})
        result = el.save()
        self.assertIn('participant_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 1)
        # if participant_vlan_id is a valid VLAN id, this is ok
        v = VLAN({'number': 1, 'purpose': 2})
        v.save()
        el = Switch({'addr': 'sw3', 'participant_vlan_id': v['_id']})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 2)

    def test_participant_vlan_id_purpose_onboarding(self):
        # vlan needs to be of purpose 2 (onboarding)
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 0, this is not ok
        v = VLAN({'number': 1, 'purpose': 0})
        v.save()
        el = Switch({'addr': 'sw1', 'participant_vlan_id': v['_id']})
        result = el.save()
        self.assertIn('participant_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 1, this is not ok
        v = VLAN({'number': 2, 'purpose': 1})
        v.save()
        el = Switch({'addr': 'sw2', 'participant_vlan_id': v['_id']})
        result = el.save()
        self.assertIn('participant_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 3, this is not ok
        v = VLAN({'number': 3, 'purpose': 3})
        v.save()
        el = Switch({'addr': 'sw3', 'participant_vlan_id': v['_id']})
        result = el.save()
        self.assertIn('participant_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 2, this is finally ok
        v = VLAN({'number': 4, 'purpose': 2})
        v.save()
        el = Switch({'addr': 'sw4', 'participant_vlan_id': v['_id']})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)


setup_module = setUpModule
teardown_module = tearDownModule


class TestSwitchApi(ApiTestBase):
    _element = Switch
    _path = 'switch'
    _patch_valid = {'purpose': 2}
    _patch_invalid = {'purpose': -1}

    def setUp(self):
        docDB.clear()
        self._setup_el1 = {'addr': 'switch1'}
        self._setup_el2 = {'addr': 'switch2'}
        self._post_valid = {'addr': 'switch3'}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
