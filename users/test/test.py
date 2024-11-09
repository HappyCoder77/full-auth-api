import unittest
from unittest.mock import Mock, patch
from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from ..authentication import CustomJWTAuthentication


class TestCustomJWTAuthentication(unittest.TestCase):
    # TODO: Estudiar este codigo, se copió asi sin mas de la IA
    @patch('users.authentication.CustomJWTAuthentication.get_header')
    @patch('users.authentication.CustomJWTAuthentication.get_raw_token')
    @patch('users.authentication.CustomJWTAuthentication.get_validated_token')
    @patch('users.authentication.CustomJWTAuthentication.get_user')
    def test_authenticate_with_header(self, mock_get_user, mock_get_validated_token, mock_get_raw_token, mock_get_header):
        request = Mock()
        mock_get_header.return_value = 'header_token'
        mock_get_raw_token.return_value = 'raw_token'
        mock_get_validated_token.return_value = 'validated_token'
        mock_get_user.return_value = 'user'

        auth = CustomJWTAuthentication()
        user, token = auth.authenticate(request)

        self.assertEqual(user, 'user')
        self.assertEqual(token, 'validated_token')
        mock_get_header.assert_called_once_with(request)
        mock_get_raw_token.assert_called_once_with('header_token')
        mock_get_validated_token.assert_called_once_with('raw_token')
        mock_get_user.assert_called_once_with('validated_token')

    @patch('users.authentication.CustomJWTAuthentication.get_header')
    @patch('users.authentication.CustomJWTAuthentication.get_validated_token')
    @patch('users.authentication.CustomJWTAuthentication.get_user')
    def test_authenticate_with_cookie(self, mock_get_user, mock_get_validated_token, mock_get_header):
        request = Mock()
        request.COOKIES = {settings.AUTH_COOKIE: 'cookie_token'}
        mock_get_header.return_value = None
        mock_get_validated_token.return_value = 'validated_token'
        mock_get_user.return_value = 'user'

        auth = CustomJWTAuthentication()
        user, token = auth.authenticate(request)

        self.assertEqual(user, 'user')
        self.assertEqual(token, 'validated_token')
        mock_get_header.assert_called_once_with(request)
        mock_get_validated_token.assert_called_once_with('cookie_token')
        mock_get_user.assert_called_once_with('validated_token')

    @patch('users.authentication.CustomJWTAuthentication.get_header')
    def test_authenticate_no_token(self, mock_get_header):
        request = Mock()
        mock_get_header.return_value = None
        request.COOKIES = {}

        auth = CustomJWTAuthentication()
        result = auth.authenticate(request)

        self.assertIsNone(result)
        mock_get_header.assert_called_once_with(request)

    @patch('users.authentication.CustomJWTAuthentication.get_header')
    @patch('users.authentication.CustomJWTAuthentication.get_raw_token')
    @patch('users.authentication.CustomJWTAuthentication.get_validated_token')
    def test_authenticate_invalid_token(self, mock_get_validated_token, mock_get_raw_token, mock_get_header):
        request = Mock()
        mock_get_header.return_value = 'header_token'
        mock_get_raw_token.return_value = 'raw_token'
        mock_get_validated_token.side_effect = InvalidToken()

        auth = CustomJWTAuthentication()
        result = auth.authenticate(request)

        self.assertIsNone(result)
        mock_get_header.assert_called_once_with(request)
        mock_get_raw_token.assert_called_once_with('header_token')
        mock_get_validated_token.assert_called_once_with('raw_token')

    @patch('users.authentication.CustomJWTAuthentication.get_header')
    @patch('users.authentication.CustomJWTAuthentication.get_raw_token')
    @patch('users.authentication.CustomJWTAuthentication.get_validated_token')
    def test_authenticate_authentication_failed(self, mock_get_validated_token, mock_get_raw_token, mock_get_header):
        request = Mock()
        mock_get_header.return_value = 'header_token'
        mock_get_raw_token.return_value = 'raw_token'
        mock_get_validated_token.side_effect = AuthenticationFailed()

        auth = CustomJWTAuthentication()
        result = auth.authenticate(request)

        self.assertIsNone(result)
        mock_get_header.assert_called_once_with(request)
        mock_get_raw_token.assert_called_once_with('header_token')
        mock_get_validated_token.assert_called_once_with('raw_token')

    def test_authenticate_header(self):
        request = Mock()
        auth = CustomJWTAuthentication()
        header = auth.authenticate_header(request)
        self.assertEqual(header, 'Bearer')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
