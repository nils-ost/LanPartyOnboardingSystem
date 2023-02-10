import unittest
from datetime import datetime
from helpers.docdb import docDB
from elements import Session, Participant
from testcases._wrapper import setUpModule, tearDownModule, ApiBase


class TestSession(unittest.TestCase):
    def setUp(self):
        docDB.clear()
        # Participant
        self.p1_id = Participant({'login': 'p1'}).save().get('created')

    def test_participant_id_FK_and_notnone(self):
        self.assertEqual(len(Session.all()), 0)
        # participant_id can't be None
        el = Session({'till': int(datetime.now().timestamp() + 60), 'ip': '127.0.0.1', 'participant_id': None})
        self.assertIn('participant_id', el.save()['errors'])
        self.assertEqual(len(Session.all()), 0)
        # participant_id can't be a random string
        el = Session({'till': int(datetime.now().timestamp() + 60), 'ip': '127.0.0.1', 'participant_id': 'somerandomstring'})
        self.assertIn('participant_id', el.save()['errors'])
        self.assertEqual(len(Session.all()), 0)
        # but a valid participant_id can be stored
        el = Session({'till': int(datetime.now().timestamp() + 60), 'ip': '127.0.0.1', 'participant_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Session.all()), 1)

    def test_till_in_the_future(self):
        self.assertEqual(len(Session.all()), 0)
        # can't be now
        el = Session({'till': int(datetime.now().timestamp()), 'ip': '127.0.0.1', 'participant_id': self.p1_id})
        self.assertIn('till', el.save()['errors'])
        self.assertEqual(len(Session.all()), 0)
        # can't be in the past
        el = Session({'till': int(datetime.now().timestamp() - 1), 'ip': '127.0.0.1', 'participant_id': self.p1_id})
        self.assertIn('till', el.save()['errors'])
        self.assertEqual(len(Session.all()), 0)
        # can only be in the future
        el = Session({'till': int(datetime.now().timestamp() + 2), 'ip': '127.0.0.1', 'participant_id': self.p1_id})
        self.assertNotIn('errors', el.save())
        self.assertEqual(len(Session.all()), 1)


setup_module = setUpModule
teardown_module = tearDownModule


class TestSessionApi(ApiBase):
    _path = 'session'

    def test_options_all(self):
        result = self.webapp_request(path=f'/{self._path}/', method='OPTIONS')
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')

    def test_get_all(self):
        result = self.webapp_request(path=f'/{self._path}/', method='GET')
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')

    def test_post_all(self):
        result = self.webapp_request(path=f'/{self._path}/', method='POST', data={})
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')
