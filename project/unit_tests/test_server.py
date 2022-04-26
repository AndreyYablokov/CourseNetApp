import sys
import os
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.constants import ACTION, PRESENCE, TIME, TYPE, STATUS, RESPONSE, ERROR, USER, ACCOUNT_NAME
from server import process_client_message, get_command_line_params


class TestServer(unittest.TestCase):
    message_ok = {RESPONSE: 200}
    message_error = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_right_client_presence_message(self):
        """Тестирует работу функции process_client_message при корректном сообщении от клиента"""
        presence_message = {
            ACTION: PRESENCE,
            TIME: 1.0,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: "Guest",
                STATUS: 'I am here!'
            }
        }
        self.assertEqual(process_client_message(presence_message), self.message_ok)

    def test_client_presence_message_no_action(self):
        """Тестирует работу функции process_client_message при некорректном сообщении от клиента"""
        presence_message = {
            TIME: 1.0,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: "Guest",
                STATUS: 'I am here!'
            }
        }
        self.assertEqual(process_client_message(presence_message), self.message_error)

    def test_client_presence_message_wrong_action(self):
        """Тестирует работу функции process_client_message при некорректном сообщении от клиента"""
        presence_message = {
            ACTION: "This is wrong action!",
            TIME: 1.0,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: "Guest",
                STATUS: 'I am here!'
            }
        }
        self.assertEqual(process_client_message(presence_message), self.message_error)

    def test_client_presence_message_no_time(self):
        """Тестирует работу функции process_client_message при некорректном сообщении от клиента"""
        presence_message = {
            ACTION: PRESENCE,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: "Guest",
                STATUS: 'I am here!'
            }
        }
        self.assertEqual(process_client_message(presence_message), self.message_error)

    def test_client_presence_message_no_user(self):
        """Тестирует работу функции process_client_message при некорректном сообщении от клиента"""
        presence_message = {
            ACTION: PRESENCE,
            TIME: 1.0,
            TYPE: STATUS,
        }
        self.assertEqual(process_client_message(presence_message), self.message_error)

    def test_client_presence_message_wrong_user(self):
        """Тестирует работу функции process_client_message при некорректном сообщении от клиента"""
        presence_message = {
            ACTION: PRESENCE,
            TIME: 1.0,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: "This is wrong user",
                STATUS: 'I am here!'
            }
        }
        self.assertEqual(process_client_message(presence_message), self.message_error)

    @patch.object(sys, 'argv', ['server_main.py', '-a', '192.168.0.1', '-p', '1024'])
    def test_get_command_line_params_ok_with_IP_port(self):
        """Тестирует работу функции get_command_line_params"""
        valid_result = {
            'listen_port': 1024,
            'listen_address': '192.168.0.1',
        }
        self.assertEqual(get_command_line_params(), valid_result)

    @patch.object(sys, 'argv', ['server_main.py', '-p'])
    def test_get_command_line_params_no_port(self):
        """Тестирует работу функции get_command_line_params"""
        self.assertRaises(IndexError, get_command_line_params)

    @patch.object(sys, 'argv', ['server_main.py', '-a'])
    def test_get_command_line_params_no_address(self):
        """Тестирует работу функции get_command_line_params"""
        self.assertRaises(IndexError, get_command_line_params)

    @patch.object(sys, 'argv', ['server_main.py', '-p', '1000'])
    def test_get_command_line_params_wrong_port(self):
        """Тестирует работу функции get_command_line_params"""
        self.assertRaises(ValueError, get_command_line_params)


if __name__ == '__main__':
    unittest.main()
