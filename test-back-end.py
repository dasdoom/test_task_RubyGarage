from unittest import TestCase, main
from app import app
import requests


class TodoListTest(TestCase):

    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 302)

    def test_index_load(self):
        tester = app.test_client(self)
        response = tester.get('/sign-in', content_type='html/text')
        self.assertTrue(b'Sign In' in response.data)

    def test_incorrect_registration(self):
        tester = app.test_client(self)
        response = tester.post('/sign-up', data=dict(name='Danya', login='dasdoom', password='dasdoom1@D'), follow_redirects=True)
        self.assertTrue(b'Try another login' in response.data)

    def test_correct_registration(self):
        tester = app.test_client(self)
        response = tester.post('/sign-up', data=dict(name='test', login='testqa', password='dasdoom1@D'), follow_redirects=True)
        self.assertTrue(b'Successfuly' in response.data)

    def test_correct_log_in(self):
        tester = app.test_client(self)
        response = tester.post('/sign-in', data=dict(login='dasdoom', password='dasdoom'))
        self.assertEqual(response.status_code, 302)

    def test_incorrect_login(self):
        tester = app.test_client(self)
        response = tester.post('/sign-in', data=dict(login='dasdodasfasf', password='dasdoom'))
        self.assertTrue(b'Wrong' in response.data)

    def test_in_incorrect_pass(self):
        tester = app.test_client(self)
        response = tester.post('/sign-in', data=dict(login='dasdoom', password='dasdoom1'))
        self.assertTrue(b'Wrong' in response.data)

    def test_incorrect_url(self):
        tester = app.test_client(self)
        response = tester.get('/hi')
        self.assertEqual(response.status_code, 404)

    def test_logout(self):
        tester = app.test_client(self)
        response = tester.get('/logout')
        self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    main()
