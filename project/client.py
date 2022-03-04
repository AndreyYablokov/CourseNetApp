import sys
import socket
import json
import time
import logging
import log.client_log_config
from common.constants import DEFAULT_IP_ADDRESS, DEFAULT_PORT, ACTION, PRESENCE, \
    TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, STATUS, TYPE
from common.utils import send_message, get_message
from errors import ReqFieldMissingError
from decorators import log

logger = logging.getLogger('client_logger')


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
    logger.debug(f'Создано presence сообщение: {presence_message} для пользователя {account_name}')
    return presence_message


def process_server_message(message):
    """
    Обработка сообщения сервера
    :param message:
    :return:
    """
    logger.debug(f'Разбор сообщения {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200: OK'
        return f'400: {message[ERROR]}'
    raise ReqFieldMissingError(RESPONSE)


@log
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
        logger.critical('Неверный номер порта, номер порта должен быть из диапазона [1024;65535]')
        sys.exit(1)
    return result


def main():
    # Определяем параметры командной строки
    command_line_params = get_command_line_params()
    server_address = command_line_params['server_address']
    server_port = command_line_params['server_port']

    # Настройка сокета и запуск клиента
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_address, server_port))
        logger.info(f'Запущен клиент с параметрами: адрес сервера {server_address}, порт сервера: {server_port}')
        presence_message = create_presence_message()
        send_message(client_socket, presence_message)
        server_message = get_message(client_socket)
        server_response = process_server_message(server_message)
        logger.info(f'Принят ответ от сервера: {server_response}')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученный файл от сервера')
    except ConnectionRefusedError:
        logger.critical(f'Не удалось подключиться к серверу {server_address}. '
                        f'Конечный компьютер отверг запрос на подключение')
    except ReqFieldMissingError:
        logger.error(f'В ответет сервера отсутствуют обязательные поля:'
                     f'{ReqFieldMissingError.missing_field}')


if __name__ == '__main__':
    main()
