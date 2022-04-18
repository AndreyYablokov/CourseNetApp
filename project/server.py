import argparse
import os.path
import select
import socket
import sys
import json
import time
import logging
import log.server_log_config
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT, LIST_INFO, ADD_CONTACT, REMOVE_CONTACT, \
    GET_CONTACTS, USERS_REQUEST
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError
from decorators import log
from descriptors import ListenPort
from metaclasses import ServerVerifier
from server_database import ServerDatabase
import threading
import configparser
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, HistoryWindow, ConfigWindow, gui_create_model_active_users, gui_create_model_history
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('server_logger')

new_connection_flag = False  # Флаг нового подключения пользователя
connection_flag_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerVerifier):
    listen_port = ListenPort()

    def __init__(self, listen_address, listen_port, database):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.database = database
        self.client_sockets = []
        self.messages = []
        self.names = dict()

        super().__init__()

    def init_socket(self):
        logger.info(
            f'Запущен сервер, порт для подключений: {self.listen_port}, '
            f'адрес с которого принимаются подключения: {self.listen_address}.'
            f' Если адрес не указан, принимаются соединения с любых адресов.')
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.listen_address, self.listen_port))
        server_socket.settimeout(0.5)

        self.socket = server_socket
        self.socket.listen()

    @log
    def process_client_message(self, message, client_socket):
        global new_connection_flag
        logger.debug(f'Разбор сообщения от клиента: {message}')
        if ACTION in message and message[ACTION] == PRESENCE:
            if TIME in message and USER in message:
                if message[USER][ACCOUNT_NAME] not in self.names.keys():
                    self.names[message[USER][ACCOUNT_NAME]] = client_socket
                    client_ip_address, client_port = client_socket.getpeername()
                    self.database.user_login(message[USER][ACCOUNT_NAME], client_ip_address, client_port)
                    message = {
                        RESPONSE: 200
                    }
                    send_message(client_socket, message)
                    with connection_flag_lock:
                        new_connection_flag = True
                else:
                    message = {
                        RESPONSE: 400,
                        ERROR: 'Имя пользователя уже занято'
                    }
                    send_message(client_socket, message)
                    self.client_sockets.remove(client_socket)
                    client_socket.close()
                return

        elif ACTION in message and message[ACTION] == MESSAGE:
            if DESTINATION in message and SENDER in message and TIME in message and MESSAGE_TEXT in message:
                if self.names[message[SENDER]] == client_socket:
                    self.messages.append(message)
                    self.database.process_message(message[SENDER], message[DESTINATION])
                    return

        elif ACTION in message and message[ACTION] == EXIT:
            if ACCOUNT_NAME in message:
                if self.names[message[ACCOUNT_NAME]] == client_socket:
                    self.database.user_logout(message[ACCOUNT_NAME])
                    logger.info(f'Клиент {message[ACCOUNT_NAME]} корректно отключился от сервера')
                    self.client_sockets.remove(self.names[message[ACCOUNT_NAME]])
                    self.names[message[ACCOUNT_NAME]].close()
                    del self.names[message[ACCOUNT_NAME]]
                    with connection_flag_lock:
                        new_connection_flag = True
                    return

        elif ACTION in message and message[ACTION] == GET_CONTACTS:
            if USER in message:
                if self.names[message[USER]] == client_socket:
                    message = {
                        RESPONSE: 202,
                        LIST_INFO: self.database.get_contacts(message[USER])
                    }
                    send_message(client_socket, message)

        elif ACTION in message and message[ACTION] == ADD_CONTACT:
            if ACCOUNT_NAME in message and USER in message:
                if self.names[message[USER]] == client_socket:
                    self.database.add_contact(message[USER], message[ACCOUNT_NAME])
                    message = {
                        RESPONSE: 200,
                    }
                    send_message(client_socket, message)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT:
            if ACCOUNT_NAME in message and USER in message:
                if self.names[message[USER]] == client_socket:
                    self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
                    message = {
                        RESPONSE: 200,
                    }
                    send_message(client_socket, message)

        elif ACTION in message and message[ACTION] == USERS_REQUEST:
            if ACCOUNT_NAME in message:
                if self.names[message[ACCOUNT_NAME]] == client_socket:
                    message = {
                        RESPONSE: 202,
                        LIST_INFO: [user[0] for user in self.database.user_list()]
                    }
                    send_message(client_socket, message)
        else:
            answer = {
                RESPONSE: 400,
                ERROR: 'Запрос некорректен'
            }
            send_message(client_socket, answer)
            return

    @log
    def process_message(self, message, listen_sockets):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_sockets:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_sockets:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    def run(self):
        self.init_socket()

        while True:
            try:
                client_socket, client_address = self.socket.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соединение с клиентом: {client_address}')
                self.client_sockets.append(client_socket)

            recv_data_sockets = []
            send_data_sockets = []
            errors = []

            try:
                if self.client_sockets:
                    recv_data_sockets, send_data_sockets, errors = select.select(self.client_sockets,
                                                                                 self.client_sockets, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err}')

            if recv_data_sockets:
                for client_with_message in recv_data_sockets:
                    try:
                        message = get_message(client_with_message)
                        self.process_client_message(message, client_with_message)
                    except OSError:
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.client_sockets.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_sockets)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    logger.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.client_sockets.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
            self.messages.clear()


@log
def get_command_line_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return {
        'listen_port': listen_port,
        'listen_address': listen_address
    }


if __name__ == '__main__':
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    command_line_params = get_command_line_params()
    listen_address = command_line_params['listen_address']
    listen_port = command_line_params['listen_port']

    server_database = ServerDatabase(
        os.path.join(config['SETTINGS']['Database_path'],
                     config['SETTINGS']['Database_file'])
    )

    server = Server(listen_address, listen_port, server_database)
    server.daemon = True
    server.start()

    # Графическое окружение для сервера
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры окна
    main_window.statusBar().showMessage('Сервер работает')
    main_window.active_users_table.setModel(gui_create_model_active_users(server_database))
    main_window.active_users_table.resizeColumnsToContents()
    main_window.active_users_table.resizeRowsToContents()

    # Функция обновленния списка активных пользователей
    def active_user_update():
        global new_connection_flag
        if new_connection_flag:
            main_window.active_users_table.setModel(
                gui_create_model_active_users(server_database))
            main_window.active_users_table.resizeColumnsToContents()
            main_window.active_users_table.resizeRowsToContents()
            with connection_flag_lock:
                new_connection_flag = False

    # Функция, создающая окно со статистикой клиентов
    def show_history():
        global history_window
        history_window = HistoryWindow()
        history_window.history_table.setModel(gui_create_model_history(server_database))
        history_window.history_table.resizeColumnsToContents()
        history_window.history_table.resizeRowsToContents()
        history_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_button.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(active_user_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(active_user_update)
    main_window.show_history_button.triggered.connect(show_history)
    main_window.config_button.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()
