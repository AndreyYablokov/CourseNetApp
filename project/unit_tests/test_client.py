import sys
import os
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.constants import ACTION, PRESENCE, TIME, TYPE, STATUS, RESPONSE, ERROR, USER, ACCOUNT_NAME, DEFAULT_PORT
from client import create_presence_message, process_server_message, get_command_line_params


class TestClient(unittest.TestCase):

    def test_create_presence_message(self):
        """Тестирует работу функции create_presence_message"""
        test_presence_message = create_presence_message()
        test_presence_message[TIME] = 1.0
        valid_presence_message = {
            ACTION: PRESENCE,
            TIME: 1.0,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: "Guest",
                STATUS: 'I am here!'
            }
        }
        self.assertEqual(valid_presence_message, test_presence_message)

    def test_process_server_message_200(self):
        """Тестирует работу функции process_server_message"""
        self.assertEqual(process_server_message({RESPONSE: 200}), '200: OK')

    def test_process_server_message_400(self):
        """Тестирует работу функции process_server_message"""
        self.assertEqual(process_server_message({RESPONSE: 400, ERROR: 'Bad Request'}), '400: Bad Request')

    def test_process_server_message_no_field_response(self):
        """Тестирует работу функции process_server_message"""
        self.assertRaises(ValueError, process_server_message, {ERROR: 'Bad Request'})

    @patch.object(sys, 'argv', ['client.py', '187.212.5.240', '65534'])
    def test_get_command_line_params_ok_with_IP_port(self):
        """Тестирует работу функции get_command_line_params"""
        valid_result = {
            'server_address': '187.212.5.240',
            'server_port': 65534
        }
        self.assertEqual(get_command_line_params(), valid_result)

    @patch.object(sys, 'argv', ['client.py', '187.212.5.240'])
    def test_get_command_line_params_ok_only_IP(self):
        """Тестирует работу функции get_command_line_params"""
        valid_result = {
            'server_address': '187.212.5.240',
            'server_port': DEFAULT_PORT
        }
        self.assertEqual(get_command_line_params(), valid_result)

    @patch.object(sys, 'argv', ['client.py', '187.212.5.240', '1'])
    def test_get_command_line_params_not_valid_port(self):
        """Тестирует работу функции get_command_line_params"""
        self.assertRaises(ValueError, get_command_line_params)


if __name__ == '__main__':
    unittest.main()
