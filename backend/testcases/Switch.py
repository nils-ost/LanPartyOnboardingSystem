import unittest
from helpers.docdb import docDB
from elements import VLAN, Switch
from testcases._wrapper import ApiTestBase, setUpModule, tearDownModule


class TestSwitch(unittest.TestCase):
    def setUp(self):
        docDB.clear()

    def test_range_of_purpose(self):
        self.assertEqual(len(Switch.all()), 0)
        v = VLAN({'number': 1, 'purpose': 2})
        v.save()
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
        el2 = Switch({'addr': 'sw2', 'purpose': 3, 'onboarding_vlan_id': v['_id']})
        result = el2.save()
        self.assertIn('purpose', result['errors'])
        self.assertEqual(len(Switch.all()), 1)
        # but 2 work
        el2['purpose'] = 2
        result = el2.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 2)

    def test_onboarding_vlan_id_FK_or_None(self):
        self.assertEqual(len(Switch.all()), 0)
        # if onboarding_vlan_id is None, this is ok
        el = Switch({'addr': 'sw1', 'onboarding_vlan_id': None, 'purpose': 0})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)
        # if onboarding_vlan_id is a random string, this is not ok
        el = Switch({'addr': 'sw2', 'onboarding_vlan_id': 'somerandomstring', 'purpose': 1})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 1)
        # if onboarding_vlan_id is a valid VLAN id, this is ok
        v = VLAN({'number': 1, 'purpose': 2})
        v.save()
        el = Switch({'addr': 'sw3', 'onboarding_vlan_id': v['_id'], 'purpose': 1})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 2)

    def test_onboarding_vlan_id_purpose_onboarding(self):
        # vlan needs to be of purpose 2 (onboarding)
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 0, this is not ok
        v = VLAN({'number': 1, 'purpose': 0})
        v.save()
        el = Switch({'addr': 'sw1', 'purpose': 1, 'onboarding_vlan_id': v['_id']})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 1, this is not ok
        v = VLAN({'number': 2, 'purpose': 1})
        v.save()
        el = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': v['_id']})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 3, this is not ok
        v = VLAN({'number': 3, 'purpose': 3})
        v.save()
        el = Switch({'addr': 'sw3', 'purpose': 1, 'onboarding_vlan_id': v['_id']})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # if purpose of vlan is 2, this is finally ok
        v = VLAN({'number': 4, 'purpose': 2})
        v.save()
        el = Switch({'addr': 'sw4', 'purpose': 1, 'onboarding_vlan_id': v['_id']})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)

    def test_onboarding_vlan_id_only_used_on_one_switch(self):
        # a VLAN is only allowed to be used on one Switch
        self.assertEqual(len(Switch.all()), 0)
        v1 = VLAN({'number': 1, 'purpose': 2})
        v1.save()
        v2 = VLAN({'number': 2, 'purpose': 2})
        v2.save()
        # assign a vlan once is fine
        el = Switch({'addr': 'sw1', 'purpose': 1, 'onboarding_vlan_id': v1['_id']})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)
        # assign the vlan to another switch is not ok
        el = Switch({'addr': 'sw2', 'purpose': 1, 'onboarding_vlan_id': v1['_id']})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 1)
        # but now changing the vlan to a different one is ok
        el['onboarding_vlan_id'] = v2['_id']
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 2)
        # saving the same switch agian is also ok
        result = el.save()
        self.assertNotIn('errors', result)

    def test_onboarding_vlan_id_required_on_purposes(self):
        # if switch purpose is 1 or 2 the switch needs onboarding_vlan_id if purpose is 0 onboarding_vlan_id gets set to None
        self.assertEqual(len(Switch.all()), 0)
        v1 = VLAN({'number': 1, 'purpose': 2})
        v1.save()
        v2 = VLAN({'number': 2, 'purpose': 2})
        v2.save()
        # purpose 1 can't be saved without vlan
        el = Switch({'addr': 'sw1', 'purpose': 1, 'onboarding_vlan_id': None})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 0)
        # but purpose 1 with vlan is fine
        el['onboarding_vlan_id'] = v1['_id']
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 1)
        # purpose 2 can't be saved without vlan
        el = Switch({'addr': 'sw2', 'purpose': 2, 'onboarding_vlan_id': None})
        result = el.save()
        self.assertIn('onboarding_vlan_id', result['errors'])
        self.assertEqual(len(Switch.all()), 1)
        # but purpose 2 with vlan is fine
        el['onboarding_vlan_id'] = v2['_id']
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 2)
        # purpose 0 can be saved without vlan
        el = Switch({'addr': 'sw3', 'purpose': 0, 'onboarding_vlan_id': None})
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertEqual(len(Switch.all()), 3)
        # also setting a vlan is deleting it on save if purpose is 0
        el['onboarding_vlan_id'] = v2['_id']
        self.assertIsNotNone(el['onboarding_vlan_id'])
        result = el.save()
        self.assertNotIn('errors', result)
        self.assertIsNone(el['onboarding_vlan_id'])


setup_module = setUpModule
teardown_module = tearDownModule


class TestSwitchApi(ApiTestBase):
    _element = Switch
    _path = 'switch'
    _patch_valid = {'user': 'auser'}
    _patch_invalid = {'purpose': -1}
    _restricted_read = True
    _restricted_write = True

    def setUp(self):
        docDB.clear()
        self._setup_el1 = {'addr': 'switch1', 'purpose': 0}
        self._setup_el2 = {'addr': 'switch2', 'purpose': 0}
        self._post_valid = {'addr': 'switch3', 'purpose': 0}
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')
