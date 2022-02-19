import socket
import sys
import json
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT
from common.utils import get_message, send_message


def process_client_message(message):
    """
    Обработать сообщение клиента
    :param message:
    :return:
    """
    if ACTION in message and message[ACTION] == PRESENCE:
        if TIME in message and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
            return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


def get_command_line_params():
    # Определяем порт
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        raise IndexError('После параметра -p необходимо указать номер порта')
    except ValueError:
        raise ValueError('Номер порта должен быть из диапазоне [1024;65535]')

    # Определяем адрес
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        raise IndexError('После параметра -a необходимо указать адрес, который будет слушать сервер')

    return {
        'listen_port': listen_port,
        'listen_address': listen_address
    }


def main():
    # Определение параметров коммандной строки
    command_line_params = get_command_line_params()
    listen_address = command_line_params['listen_address']
    listen_port = command_line_params['listen_port']

    # Настройка сокета и запуск сервера
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((listen_address, listen_port))
    server_socket.listen(MAX_CONNECTIONS)
    while True:
        client_socket, client_address = server_socket.accept()
        try:
            client_message = get_message(client_socket)
            print(client_message)
            server_response = process_client_message(client_message)
            send_message(client_socket, server_response)
            client_socket.close()
        except (ValueError, json.JSONDecodeError):
            print('Принято некорректное сообщение от клиента')
            client_socket.close()


if __name__ == '__main__':
    main()
