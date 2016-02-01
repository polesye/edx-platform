"""
Tests for Blocks Views
"""

import json

import ddt
from django.test import TestCase, RequestFactory
from mock import patch
from oauth2_provider.models import Application
from provider import constants
from provider.oauth2.models import Client
from student.tests.factories import UserFactory

from .. import views


@ddt.ddt
class TestAccessTokenView(TestCase):
    """
    Test class for AccessTokenView
    """

    def setUp(self):
        super(TestAccessTokenView, self).setUp()
        self.user = UserFactory()
        self.dot_app = Application.objects.create(
            user_id=self.user.id,  # pylint: disable=no-member
            redirect_uris='/',
            client_type='public',
            authorization_grant_type='password',
        )
        self.dop_client = Client.objects.create(
            user_id=self.user.id,  # pylint: disable=no-member
            redirect_uri='/',
            client_type=constants.PUBLIC,
        )

    def test_dot_application_gets_client_id(self):
        self.assertGreater(len(self.dot_app.client_id), 0)

    def test_dop_client_gets_client_id(self):
        self.assertGreater(len(self.dop_client.client_id), 0)

    @ddt.data(
        (views.DOT_BACKEND, 'dot_app'),
        (views.DOP_BACKEND, 'dop_client'),
    )
    @ddt.unpack
    def test_access_token_fields(self, backend, client_attr):
        client = getattr(self, client_attr)
        token_view = views.AccessTokenView.as_view()
        reqfac = RequestFactory()
        request = reqfac.post('/', {
            'client_id': client.client_id,
            'grant_type': 'password',
            'username': self.user.username,
            'password': 'test',
        })
        with patch.object(views.AccessTokenView, 'select_backend', return_value=backend):
            response = token_view(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('expires_in', data)
        self.assertIn('scope', data)
        self.assertIn('token_type', data)

    def test_dot_access_token_provides_refresh_token(self):
        token_view = views.AccessTokenView.as_view()
        reqfac = RequestFactory()
        request = reqfac.post('/', {
            'client_id': self.dot_app.client_id,
            'grant_type': 'password',
            'username': self.user.username,
            'password': 'test',
        })
        with patch.object(views.AccessTokenView, 'select_backend', return_value=views.DOT_BACKEND):
            response = token_view(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('refresh_token', data)

    def test_dop_access_token(self):
        token_view = views.AccessTokenView.as_view()
        reqfac = RequestFactory()
        request = reqfac.post('/', {
            'client_id': self.dop_client.client_id,
            'grant_type': 'password',
            'username': self.user.username,
            'password': 'test',
        })
        with patch.object(views.AccessTokenView, 'select_backend', return_value=views.DOP_BACKEND):
            response = token_view(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotIn('refresh_token', data)
