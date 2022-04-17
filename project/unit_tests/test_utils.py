import sys
import os
import unittest
import json

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.constants import ENCODING, ACTION, PRESENCE, TIME, TYPE, STATUS, RESPONSE, ERROR, USER, ACCOUNT_NAME
from common.utils import get_message, send_message


class TestSocket:
    """Класс для тестирования отправки и получения сообщений через сокет"""
    def __init__(self, test_message):
        self.test_message = test_message
        self.encoded_message = None
        self.received_message = None

    def send(self, message):
        decoded_message = json.dumps(self.test_message)
        self.encoded_message = decoded_message.encode(ENCODING)
        self.received_message = message

    def recv(self, max_message_length):
        decoded_message = json.dumps(self.test_message)
        encoded_message = decoded_message.encode(ENCODING)
        return encoded_message


class TestUtils(unittest.TestCase):
    test_message = {
        ACTION: PRESENCE,
        TIME: 1.0,
        TYPE: STATUS,
        USER: {
            ACCOUNT_NAME: 'Guest',
            STATUS: 'I am here!'
        }
    }
    test_recv_ok = {RESPONSE: 200}
    test_recv_error = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_get_message_ok(self):
        """Тестирует корректность работы функции приема сообщения при сообщении без ошибок"""
        test_socket = TestSocket(self.test_recv_ok)
        received_message = get_message(test_socket)
        self.assertEqual(self.test_recv_ok, received_message)

    def test_get_message_error(self):
        """Тестирует корректность работы функции приема сообщения при сообщении с ошибками"""
        test_socket = TestSocket(self.test_recv_error)
        received_message = get_message(test_socket)
        self.assertEqual(self.test_recv_error, received_message)

    def test_get_message_not_dict(self):
        """Тестирует корректность работы функции приема сообщения при передаче данных не в виде словаря"""
        test_socket = TestSocket("This is not a dictionary")
        self.assertRaises(ValueError, get_message, test_socket)

    def test_send_message_ok(self):
        """Тестирует корректность работы функции отправки сообщения"""
        test_socket = TestSocket(self.test_message)
        send_message(test_socket, self.test_message)
        self.assertEqual(test_socket.encoded_message, test_socket.received_message)

    def test_send_message_error(self):
        """Тестирует вывод ошибки ValueError при неверных исходных данных функции отправки сообщения"""
        test_socket = TestSocket(self.test_message)
        send_message(test_socket, self.test_message)
        self.assertRaises(ValueError, send_message, test_socket, "This is not a dictionary")


if __name__ =='__main__':
    unittest.main()
