import io
import unittest
import json
import cherrypy
import hashlib
from cherrypy.lib import httputil
from main import API, docDB
from elements import Participant


def setUpModule():
    cherrypy.config.update({'environment': 'test_suite'})

    # prevent the HTTP server from ever starting
    cherrypy.server.unsubscribe()

    cherrypy.tree.mount(API(), '/')
    cherrypy.engine.start()


def tearDownModule():
    cherrypy.engine.exit()


class ApiBase(unittest.TestCase):
    _lpos_cookie = None

    def webapp_request(self, path='/', method='POST', data=None, **kwargs):
        headers = [('Host', '127.0.0.1')]
        local = httputil.Host('127.0.0.1', 50000, '')
        remote = httputil.Host('127.0.0.1', 50001, '')

        # Get our application and run the request against it
        app = cherrypy.tree.apps['']
        # Let's fake the local and remote addresses
        # Let's also use a non-secure scheme: 'http'
        request, response = app.get_serving(local, remote, 'http', 'HTTP/1.1')

        if data:
            qs = json.dumps(data)
        elif kwargs:
            qs = json.dumps(kwargs)
        else:
            qs = '{}'
        headers.append(('content-type', 'application/json'))
        if self._lpos_cookie:
            headers.append(('cookie', self._lpos_cookie))
        headers.append(('content-length', f'{len(qs)}'))
        fd = io.BytesIO(qs.encode())
        qs = None
        if '?' in path:
            path, qs = path.split('?')

        try:
            response = request.run(method.upper(), path, qs, 'HTTP/1.1', headers, fd)
            if response.cookie:
                self._lpos_cookie = str(response.cookie).replace('Set-Cookie: ', '')
        finally:
            if fd:
                fd.close()
                fd = None

        if response.output_status.startswith(b'500'):
            print(response.body)
            raise AssertionError('Unexpected error')

        # collapse the response into a bytestring
        response.collapse_body()
        try:
            response.json = json.loads(response.body[0])
        except Exception:
            response.json = {}

        return response


class ApiTestBase(ApiBase):
    def setUp(self):
        docDB.clear()
        el = self._element(self._setup_el1)
        self.id1 = el.save().get('created')
        el = self._element(self._setup_el2)
        self.id2 = el.save().get('created')

    def login_user(self):
        Participant({'login': 'testinguser', 'pw': 'hi'}).save()
        result = self.webapp_request(path='/login/?user=testinguser', method='GET').json
        m = hashlib.md5()
        m.update(result['session_id'].encode('utf-8'))
        m.update(b'hi')
        self.webapp_request(path='/login/', method='POST', data={'pw': m.hexdigest()})

    def login_admin(self):
        Participant({'login': 'testingadmin', 'pw': 'hi', 'admin': True}).save()
        result = self.webapp_request(path='/login/?user=testingadmin', method='GET').json
        m = hashlib.md5()
        m.update(result['session_id'].encode('utf-8'))
        m.update(b'hi')
        self.webapp_request(path='/login/', method='POST', data={'pw': m.hexdigest()})

    def test_options_all(self):
        self.login_user()
        result = self.webapp_request(path=f'/{self._path}/', method='OPTIONS')
        self.assertIn('OPTIONS', result.headers['Allow'])
        self.assertIn('GET', result.headers['Allow'])
        self.assertIn('POST', result.headers['Allow'])
        self.assertNotIn('PATCH', result.headers['Allow'])
        self.assertNotIn('DELETE', result.headers['Allow'])
        self.assertNotIn('PUT', result.headers['Allow'])

    def test_options_single(self):
        self.login_user()
        result = self.webapp_request(path=f'/{self._path}/something/', method='OPTIONS')
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='OPTIONS')
        self.assertIn('OPTIONS', result.headers['Allow'])
        self.assertIn('GET', result.headers['Allow'])
        self.assertNotIn('POST', result.headers['Allow'])
        self.assertIn('PATCH', result.headers['Allow'])
        self.assertIn('DELETE', result.headers['Allow'])
        self.assertNotIn('PUT', result.headers['Allow'])

    def test_get_all(self):
        self.login_user()
        if self._restricted_read:
            result = self.webapp_request(path=f'/{self._path}/', method='GET')
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        result = self.webapp_request(path=f'/{self._path}/', method='GET')
        if self._element == Participant:
            if self._restricted_read:
                self.assertEqual(len(result.json), 4)
            else:
                self.assertEqual(len(result.json), 3)
        else:
            self.assertEqual(len(result.json), 2)

    def test_get_single(self):
        self.login_user()
        if self._restricted_read:
            result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='GET')
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='GET')
        k = list(self._setup_el1.keys())[0]
        self.assertEqual(result.json[k], self._setup_el1[k])
        result = self.webapp_request(path=f'/{self._path}/something/', method='GET')
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')

    def test_post_all(self):
        self.login_user()
        if self._restricted_write:
            result = self.webapp_request(path=f'/{self._path}/', method='POST', data=self._post_valid)
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        expected_count = 2
        if self._element == Participant:
            expected_count += 1
            if self._restricted_write:
                expected_count += 1
        self.assertEqual(len(self._element.all()), expected_count)
        result = self.webapp_request(path=f'/{self._path}/', method='POST')
        self.assertTrue(result.status.startswith('400'), msg=f'should start with 400 but is {result.status}')
        self.assertEqual(len(self._element.all()), expected_count)
        result = self.webapp_request(path=f'/{self._path}/', method='POST', data=['a', 'list'])
        self.assertTrue(result.status.startswith('400'), msg=f'should start with 400 but is {result.status}')
        self.assertEqual(len(self._element.all()), expected_count)
        result = self.webapp_request(path=f'/{self._path}/', method='POST', data=self._post_valid)
        self.assertTrue(result.status.startswith('201'), msg=f'should start with 201 but is {result.status}.')
        expected_count += 1
        self.assertEqual(len(self._element.all()), expected_count)

    def test_post_single(self):
        self.login_user()
        if self._restricted_write:
            result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='POST')
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='POST')
        self.assertTrue(result.status.startswith('405'), msg=f'should start with 405 but is {result.status}')

    def test_delete_all(self):
        self.login_user()
        if self._restricted_write:
            result = self.webapp_request(path=f'/{self._path}/', method='DELETE')
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        result = self.webapp_request(path=f'/{self._path}/', method='DELETE')
        self.assertTrue(result.status.startswith('405'), msg=f'should start with 405 but is {result.status}')

    def test_delete_single(self):
        self.login_user()
        if self._restricted_write:
            result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='DELETE')
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        expected_count = 2
        if self._element == Participant:
            expected_count += 1
            if self._restricted_write:
                expected_count += 1
        self.assertEqual(len(self._element.all()), expected_count)
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='DELETE')
        expected_count -= 1
        self.assertEqual(len(self._element.all()), expected_count)
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='DELETE')
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')
        self.assertEqual(len(self._element.all()), expected_count)
        result = self.webapp_request(path=f'/{self._path}/{self.id2}/', method='DELETE')
        expected_count -= 1
        self.assertEqual(len(self._element.all()), expected_count)

    def test_patch_all(self):
        self.login_user()
        if self._restricted_write:
            result = self.webapp_request(path=f'/{self._path}/', method='PATCH')
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        result = self.webapp_request(path=f'/{self._path}/', method='PATCH')
        self.assertTrue(result.status.startswith('405'), msg=f'should start with 405 but is {result.status}')

    def test_patch_single(self):
        self.login_user()
        if self._restricted_write:
            result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='PATCH', data=self._patch_valid)
            self.assertTrue(result.status.startswith('403'), msg=f'should start with 403 but is {result.status}')
            self.login_admin()
        el = self._element.get(self.id1)
        k = list(self._patch_valid.keys())[0]
        self.assertEqual(el[k], self._element._attrdef[k]['default'])
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='PATCH', data=self._patch_valid)
        el.reload()
        k = list(self._patch_valid.keys())[0]
        self.assertEqual(el[k], self._patch_valid[k])
        result = self.webapp_request(path=f'/{self._path}/something/', method='PATCH', data=self._patch_valid)
        self.assertTrue(result.status.startswith('404'), msg=f'should start with 404 but is {result.status}')
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='PATCH', data=['a', 'list'])
        self.assertTrue(result.status.startswith('400'), msg=f'should start with 400 but is {result.status}')
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='PATCH', data=self._patch_invalid)
        self.assertTrue(result.status.startswith('400'), msg=f'should start with 400 but is {result.status}')
        el.reload()
        k = list(self._patch_invalid.keys())[0]
        self.assertNotEqual(el[k], self._patch_invalid[k])

    def test_put_all(self):
        self.login_user()
        result = self.webapp_request(path=f'/{self._path}/', method='PUT')
        self.assertTrue(result.status.startswith('405'), msg=f'should start with 405 but is {result.status}')
        self.assertIn('OPTIONS', result.headers['Allow'])
        self.assertIn('GET', result.headers['Allow'])
        self.assertIn('POST', result.headers['Allow'])

    def test_put_single(self):
        self.login_user()
        result = self.webapp_request(path=f'/{self._path}/{self.id1}/', method='PUT')
        self.assertTrue(result.status.startswith('405'), msg=f'should start with 405 but is {result.status}')
        self.assertIn('OPTIONS', result.headers['Allow'])
        self.assertIn('GET', result.headers['Allow'])
        self.assertIn('PATCH', result.headers['Allow'])
        self.assertIn('DELETE', result.headers['Allow'])
