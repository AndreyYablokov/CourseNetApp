import select
import socket
import sys
import json
import time
import logging
import log.server_log_config
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError
from decorators import log

logger = logging.getLogger('server_logger')


def process_client_message(message, messages, client_socket):
    """
    Обработать сообщение клиента
    :param message:
    :return:
    """
    logger.debug(f'Разбор сообщения от клиента: {message}')
    if ACTION in message and message[ACTION] == PRESENCE:
        if TIME in message and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
            answer = {RESPONSE: 200}
            send_message(client_socket, answer)
            return
    elif ACTION in message and message[ACTION] == MESSAGE:
        if TIME in message and MESSAGE_TEXT in message:
            messages.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
            return
    else:
        answer = {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        }
        send_message(client_socket, answer)
        return


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
                    process_client_message(message, messages, client_with_message)
                except:
                    logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                    client_sockets.remove(client_with_message)

        if messages and send_data_sockets:
            message = {
                ACTION: MESSAGE,
                SENDER: messages[0][0],
                TIME: time.time(),
                MESSAGE_TEXT: messages[0][1]
            }
            del messages[0]
            for waiting_client in send_data_sockets:
                try:
                    send_message(waiting_client, message)
                except:
                    logger.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    waiting_client.close()
                    client_sockets.remove(waiting_client)

        # try:
        #     client_message = get_message(client_socket)
        #     logger.debug(f'Получено сообщение: {client_message}')
        #     server_response = process_client_message(client_message)
        #     logger.info(f'Сформирован ответ клиенту: {server_response}')
        #     send_message(client_socket, server_response)
        #     client_socket.close()
        #     logger.debug(f'Соединение с клиентом {client_address} разорвано')
        # except json.JSONDecodeError:
        #     logger.error(f'Не удалось декодировать сообщение от клиента {client_address}')
        #     client_socket.close()
        # except IncorrectDataRecivedError:
        #     logger.error(f'Прнияты некорректные данные от клиента {client_address}')
        #     client_socket.close()


if __name__ == '__main__':
    main()
