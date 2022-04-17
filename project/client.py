import sys
import socket
import json
import threading
import time
import argparse
import logging
import log.client_log_config
from common.constants import DEFAULT_IP_ADDRESS, DEFAULT_PORT, ACTION, PRESENCE, \
    TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, STATUS, TYPE, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from common.utils import send_message, get_message
from errors import ReqFieldMissingError, IncorrectDataRecivedError
from decorators import log
from metaclasses import ClientVerifier

logger = logging.getLogger('client_logger')


class Client(metaclass=ClientVerifier):
    def __init__(self,  server_address, server_port, client_name):
        self.server_address = server_address
        self.server_port = server_port
        self.client_name = client_name
        self.socket = ''

    @log
    def create_presence_message(self):
        """
        Создать сообщение о присутствии клиента
        :return:
        """
        presence_message = {
            ACTION: PRESENCE,
            TIME: time.time(),
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: self.client_name,
                STATUS: 'I am here!'
            }
        }
        logger.debug(f'Создано presence сообщение: {presence_message} для пользователя {self.client_name}')
        return presence_message

    @log
    def create_user_message(self):
        receiver = input('Введите имя аккаунта получателя сообщания: ')
        client_message = input('Введите сообщение для отправки: ')
        message = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: client_message
        }
        logger.debug(f'Создано обычное сообщение: {message} для пользователя {self.client_name}')
        return message

    @log
    def create_exit_message(self):
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name,
        }
        logger.debug(f'Создано сообщение о выходе пользователя {self.client_name}')
        return message

    @log
    def receive_message(self):
        while True:
            try:
                message = get_message(self.socket)
                if ACTION in message and message[ACTION] == MESSAGE:
                    if SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                              f'\n {message[MESSAGE_TEXT]}')
                        logger.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                    f'\n {message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                logger.error('Не удалось декодировать полученное от сервера сообщение')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical('Потеряно соединение с сервером')
                break

    @staticmethod
    @log
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
    def user_interactive(self):
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                message = self.create_user_message()
                try:
                    send_message(self.socket, message)
                except Exception:
                    logger.critical('Потеряно соединение с сервером')
                    sys.exit(1)
                logger.info(f'Отправлено сообщение для пользователя {message[DESTINATION]}')
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                message = self.create_exit_message()
                try:
                    send_message(self.socket, message)
                except Exception:
                    logger.critical('Потеряно соединение с сервером')
                    sys.exit(1)
                print('Завершение соединения')
                logger.info('Завершение работы по команде пользователя')
                time.sleep(1)
                break
            else:
                print('Команда не распознана. Введите help для получения справки по доступным командам')

    @staticmethod
    def print_help():
        print('Поддерживаемые команды: ')
        print('message - отправить сообщение')
        print('help - вывести справку')
        print('exit - завершить работу')

    def run(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_address, self.server_port))
            logger.info(f'Запущен клиент с параметрами: адрес сервера {self.server_address},'
                        f' порт сервера: {self.server_port}')
            presence_message = self.create_presence_message()
            send_message(self.socket, presence_message)
            server_message = get_message(self.socket)
            server_response = self.process_server_message(server_message)
            logger.info(f'Установлено соединение с сервером. Принят ответ от сервера: {server_response}')
        except json.JSONDecodeError:
            logger.error('Не удалось декодировать полученный файл от сервера')
        except (ConnectionRefusedError, ConnectionError):
            logger.critical(f'Не удалось подключиться к серверу {self.server_address}. '
                            f'Конечный компьютер отверг запрос на подключение')
        except ReqFieldMissingError:
            logger.error(f'В ответет сервера отсутствуют обязательные поля:'
                         f'{ReqFieldMissingError.missing_field}')
        else:
            receiver_thread = threading.Thread(target=self.receive_message)
            receiver_thread.daemon = True
            receiver_thread.start()

            user_interface_thread = threading.Thread(target=self.user_interactive)
            user_interface_thread.daemon = True
            user_interface_thread.start()

            while True:
                time.sleep(1)
                if receiver_thread.is_alive() and user_interface_thread.is_alive():
                    continue
                break


@log
def get_command_line_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('server_address', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('server_port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])

    result = {
        'server_address': namespace.server_address,
        'server_port': namespace.server_port,
        'client_name': namespace.name
    }

    if result['server_port'] < 1024 or result['server_port'] > 65535:
        logger.critical('Неверный номер порта, номер порта должен быть из диапазона [1024;65535]')
        sys.exit(1)

    return result


if __name__ == '__main__':
    command_line_params = get_command_line_params()
    server_address = command_line_params['server_address']
    server_port = command_line_params['server_port']
    client_name = command_line_params['client_name']

    print('Вас приветствует консольный месенджер')

    if not client_name:
        client_name = input('Введите имя пользователя: ')

    print(f'Имя пользователя: {client_name}')

    client = Client(server_address, server_port, client_name)
    client.run()
