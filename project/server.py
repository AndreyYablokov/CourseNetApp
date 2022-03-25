import select
import socket
import sys
import json
import time
import logging
import log.server_log_config
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError
from decorators import log

logger = logging.getLogger('server_logger')


def process_client_message(message, messages, client_socket, client_sockets, names):
    """
    Обработать сообщение клиента
    :param message:
    :return:
    """
    logger.debug(f'Разбор сообщения от клиента: {message}')
    if ACTION in message and message[ACTION] == PRESENCE:
        if TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client_socket
                message = {
                    RESPONSE: 200
                }
                send_message(client_socket, message)
            else:
                message = {
                    RESPONSE: 400,
                    ERROR: 'Имя пользователя уже занято'
                }
                send_message(client_socket, message)
                client_sockets.remove(client_socket)
                client_socket.close()
            return
    elif ACTION in message and message[ACTION] == MESSAGE:
        if DESTINATION in message and SENDER in message and TIME in message and MESSAGE_TEXT in message:
            messages.append(message)
            return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        client_sockets.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    else:
        answer = {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        }
        send_message(client_socket, answer)
        return


@log
def process_message(message, names, listen_sockets):
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_sockets:
        send_message(names[message[DESTINATION]], message)
        logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                    f'от пользователя {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_sockets:
        raise ConnectionError
    else:
        logger.error(
            f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.')


@log
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
        logger.error('После параметра -p не указан номер порта при запуске скрипта')
    except ValueError:
        logger.critical('Неверный номер порта, номер порта должен быть из диапазона [1024;65535]')
        sys.exit(1)

    # Определяем адрес
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        logger.error('После параметра -a не указан адрес, который будет слушать сервер')

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
    logger.info(f'Запущен сервер. Адрес, с которого принимаются подключения: {listen_address}.'
                f'Порт для подключений: {listen_port}')
    server_socket.settimeout(1)

    client_sockets = []
    messages = []
    names = dict()

    server_socket.listen(MAX_CONNECTIONS)
    while True:
        try:
            client_socket, client_address = server_socket.accept()
        except OSError:
            print(OSError.errno)
        else:
            logger.info(f'Установлено соединение с клиентом: {client_address}')
            client_sockets.append(client_socket)

        recv_data_sockets = []
        send_data_sockets = []
        errors = []

        try:
            if client_sockets:
                recv_data_sockets, send_data_sockets, errors = select.select(client_sockets, client_sockets, [], 0)
        except OSError:
            pass

        if recv_data_sockets:
            for client_with_message in recv_data_sockets:
                try:
                    message = get_message(client_with_message)
                    process_client_message(message, messages, client_with_message, client_sockets, names)
                except Exception:
                    logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                    client_sockets.remove(client_with_message)

        for message in messages:
            try:
                process_message(message, names, send_data_sockets)
            except Exception:
                logger.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                client_sockets.remove(names[message[DESTINATION]])
                del names[message[DESTINATION]]
        messages.clear()


if __name__ == '__main__':
    main()
