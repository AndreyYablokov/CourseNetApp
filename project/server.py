import socket
import sys
import json
import logging
import log.server_log_config
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError

logger = logging.getLogger('server_logger')


def process_client_message(message):
    """
    Обработать сообщение клиента
    :param message:
    :return:
    """
    logger.debug(f'Разбор сообщения от клиента: {message}')
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
    server_socket.listen(MAX_CONNECTIONS)
    while True:
        client_socket, client_address = server_socket.accept()
        logger.info(f'Установлено соединение с клиентом: {client_address}')
        try:
            client_message = get_message(client_socket)
            logger.debug(f'Получено сообщение: {client_message}')
            server_response = process_client_message(client_message)
            logger.info(f'Сформирован ответ клиенту: {server_response}')
            send_message(client_socket, server_response)
            client_socket.close()
            logger.debug(f'Соединение с клиентом {client_address} разорвано')
        except json.JSONDecodeError:
            logger.error(f'Не удалось декодировать сообщение от клиента {client_address}')
            client_socket.close()
        except IncorrectDataRecivedError:
            logger.error(f'Прнияты некорректные данные от клиента {client_address}')
            client_socket.close()


if __name__ == '__main__':
    main()
