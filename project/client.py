import sys
import socket
import json
import time
from common.constants import DEFAULT_IP_ADDRESS, DEFAULT_PORT, ACTION, PRESENCE, \
    TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, STATUS, TYPE
from common.utils import send_message, get_message


def create_presence_message(account_name='Guest'):
    """
    Создать сообщение о присутствии клиента
    :return:
    """
    presence_message = {
        ACTION: PRESENCE,
        TIME: time.time(),
        TYPE: STATUS,
        USER: {
            ACCOUNT_NAME: account_name,
            STATUS: 'I am here!'
        }
    }
    return presence_message


def process_server_message(message):
    """
    Обработка сообщения сервера
    :param message:
    :return:
    """
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200: OK'
        return f'400: {message[ERROR]}'
    raise ValueError


def get_command_line_params():
    result = {
        'server_address': DEFAULT_IP_ADDRESS,
        'server_port': DEFAULT_PORT
    }
    if len(sys.argv) > 1:
        result['server_address'] = sys.argv[1]
    if len(sys.argv) > 2:
        result['server_port'] = int(sys.argv[2])
    if result['server_port'] < 1024 or result['server_port'] > 65535:
        raise ValueError('Неверный номер порта, номер порта должен быть из диапазона [1024;65535]')
    return result


def main():
    # Определяем параметры командной строки
    command_line_params = get_command_line_params()
    server_address = command_line_params['server_address']
    server_port = command_line_params['server_port']

    # Настройка сокета и запуск клиента
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_address, server_port))
    presence_message = create_presence_message()
    send_message(client_socket, presence_message)
    try:
        server_message = get_message(client_socket)
        server_response = process_server_message(server_message)
        print(server_response)
    except (ValueError, json.JSONDecodeError):
        print('Принято некорректное сообщение от сервера')


if __name__ == '__main__':
    main()
