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


def main():

    # Определяем порт
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('После параметра -p необходимо указать номер порта')
        sys.exit(1)
    except ValueError:
        print('Номер порта должен быть из диапазоне [1024;65535]')
        sys.exit(1)

    # Определяем адрес
    try:
        if '-a' in sys.argv:
            listen_address = int(sys.argv[sys.argv.index('-a') + 1])
        else:
            listen_address = ''
    except IndexError:
        print('После параметра -a необходимо указать адрес, который будет слушать сервер')
        sys.exit(1)

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
