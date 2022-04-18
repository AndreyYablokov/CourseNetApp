import sys
import socket
import json
import threading
import time
import argparse
import logging
import log.client_log_config
from common.constants import DEFAULT_IP_ADDRESS, DEFAULT_PORT, ACTION, PRESENCE, \
    TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, STATUS, TYPE, MESSAGE, MESSAGE_TEXT, \
    SENDER, DESTINATION, EXIT, GET_CONTACTS, LIST_INFO, ADD_CONTACT, REMOVE_CONTACT, \
    USERS_REQUEST
from common.utils import send_message, get_message
from errors import ReqFieldMissingError, IncorrectDataRecivedError, ServerError
from decorators import log
from metaclasses import ClientVerifier
from client_database import ClientDatabase

logger = logging.getLogger('client_logger')

socket_lock = threading.Lock()
database_lock = threading.Lock()


class Client(metaclass=ClientVerifier):
    def __init__(self,  server_address, server_port, client_name, database):
        self.server_address = server_address
        self.server_port = server_port
        self.client_name = client_name
        self.socket = ''
        self.database = database

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

        with database_lock:
            if not self.database.check_user(receiver):
                logger.error(f'Попытка отправить сообщение незарегистрированному пользователю: {receiver}')
                return

        message = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: client_message
        }
        logger.debug(f'Создано обычное сообщение: {message} для пользователя {self.client_name}')
        with database_lock:
            self.database.save_message(self.client_name, receiver, client_message)

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
            time.sleep(1)
            with socket_lock:
                try:
                    message = get_message(self.socket)
                    if ACTION in message and message[ACTION] == MESSAGE:
                        if SENDER in message and DESTINATION in message \
                                and MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
                            print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                                  f'\n {message[MESSAGE_TEXT]}')
                            logger.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                        f'\n {message[MESSAGE_TEXT]}')
                            with database_lock:
                                try:
                                    self.database.save_message(message[SENDER],
                                                               self.client_name,
                                                               message[MESSAGE_TEXT])
                                except Exception as e:
                                    print(e)
                                    logger.error('Ошибка взаимодействия с базой данных')
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
        """
        logger.debug(f'Разбор сообщения {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200: OK'
            elif message[RESPONSE] == 400:
                raise ServerError(f'400: {message[ERROR]}')
        raise ReqFieldMissingError(RESPONSE)

    @log
    def user_interactive(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                message = self.create_user_message()
                with socket_lock:
                    try:
                        send_message(self.socket, message)
                        logger.info(f'Отправлено сообщение для пользователя {message[DESTINATION]}')
                    except OSError as err:
                        if err.errno:
                            logger.critical('Потеряно соединение с сервером.')
                            sys.exit(1)
                        else:
                            logger.error('Не удалось передать сообщение. Таймаут соединения')
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                message = self.create_exit_message()
                with socket_lock:
                    try:
                        send_message(self.socket, message)
                    except Exception:
                        logger.critical('Потеряно соединение с сервером')
                        sys.exit(1)
                    print('Завершение соединения')
                    logger.info('Завершение работы по команде пользователя')
                    time.sleep(0.5)
                    break
            elif command == 'contacts':
                with database_lock:
                    contacts = self.database.get_contacts()
                for contact in contacts:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана. Введите help для получения справки по доступным командам')

    @staticmethod
    def print_help():
        print('Поддерживаемые команды: ')
        print('message - отправить сообщение')
        print('history - история сооющений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести справку')
        print('exit - завершить работу')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(recipient=self.client_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(sender=self.client_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            contact = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(contact):
                with database_lock:
                    self.database.add_contact(contact)
                with socket_lock:
                    try:
                        self.add_contact(contact)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')

    def contacts_request(self):
        logger.debug(f'Запрос контакт листа для пользователя {self.client_name}')
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.client_name
        }
        logger.debug(f'Сформирован запрос {message}')
        send_message(self.socket, message)
        answer = get_message(self.socket)
        logger.debug(f'Получен ответ {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError

    def add_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        message = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        send_message(self.socket, message)
        answer = get_message(self.socket)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка создания контакта')
        print('Удачное создание контакта.')

    def remove_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        message = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.client_name,
            ACCOUNT_NAME: contact
        }
        send_message(self.socket, message)
        answer = get_message(self.socket)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка удаления клиента')
        print('Удачное удаление')

    def users_request(self):
        logger.debug(f'Запрос списка известных пользователей {self.client_name}')
        message = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }
        send_message(self.socket, message)
        answer = get_message(self.socket)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError

    def database_load(self):
        # Загружаем список известных пользователей
        try:
            users = self.users_request()
        except ServerError:
            logger.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(users)

        # Загружаем список контактов
        try:
            contacts = self.contacts_request()
        except ServerError:
            logger.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts:
                self.database.add_contact(contact)

    def run(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(1)
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
            exit(1)
        except (ConnectionRefusedError, ConnectionError):
            logger.critical(f'Не удалось подключиться к серверу {self.server_address}. '
                            f'Конечный компьютер отверг запрос на подключение')
            exit(1)
        except ReqFieldMissingError:
            logger.error(f'В ответет сервера отсутствуют обязательные поля:'
                         f'{ReqFieldMissingError.missing_field}')
            exit(1)
        except socket.error as socketerror:
            print("Error: ", socketerror)
            exit(1)
        else:
            self.database_load()

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

    database = ClientDatabase(client_name)

    client = Client(server_address, server_port, client_name, database)
    client.run()
