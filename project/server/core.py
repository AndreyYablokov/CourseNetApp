import argparse
import binascii
import hmac
import json
import os.path
import select
import socket
import sys
import logging
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT, LIST_INFO, ADD_CONTACT, REMOVE_CONTACT, \
    GET_CONTACTS, USERS_REQUEST, MAX_CONNECTIONS, DATA, PUBLIC_KEY_REQUEST, PUBLIC_KEY
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import ListenPort
from common.metaclasses import ServerVerifier
from server.database import ServerDatabase
import threading
import configparser
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server.main_window import MainWindow, HistoryWindow, ConfigWindow

logger = logging.getLogger('server_logger')


class MessageProcessor(threading.Thread):
    listen_port = ListenPort()

    def __init__(self, listen_address, listen_port, database):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.database = database
        self.socket = None
        self.client_sockets = []
        self.listen_sockets = None
        self.error_sockets = None
        self.running = True
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
        self.socket.listen(MAX_CONNECTIONS)

    def run(self):
        self.init_socket()

        while self.running:
            try:
                client_socket, client_address = self.socket.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соединение с клиентом: {client_address}')
                client_socket.settimeout(5)
                self.client_sockets.append(client_socket)

            recv_data_sockets = []
            send_data_sockets = []
            errors = []

            try:
                if self.client_sockets:
                    recv_data_sockets, self.listen_sockets, self.error_sockets = select.select(
                        self.client_sockets, self.client_sockets, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err.errno}')

            if recv_data_sockets:
                for client_with_message in recv_data_sockets:
                    try:
                        message = get_message(client_with_message)
                        self.process_client_message(message, client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.info(f'Ошибка получения данных от клиента: {client_with_message.getpeername()}')
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        '''
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        '''
        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.client_sockets.remove(client)
        client.close()

    def autorize_user(self, message, sock):
        """ Метод реализующий авторизацию пользователей. """
        logger.debug(f'Начат процесс авторизации пользователя {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = {
                RESPONSE: 400,
                ERROR: 'Имя пользователя уже занято'
            }
            try:
                logger.debug(f'Имя пользователя занято, отправлен ответ: {response}')
                send_message(sock, response)
            except OSError:
                logger.debug('OS Error')
                pass
            self.client_sockets.remove(sock)
            sock.close()

        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = {
                RESPONSE: 400,
                ERROR: 'Пользователь не зарегистрирован'
            }
            try:
                logger.debug(f'Неизвестный пользователь, отправлен ответ: {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.client_sockets.remove(sock)
            sock.close()
        else:
            logger.debug('Корректное имя пользователя, начат процесс авторизации')

            message_auth = {
                RESPONSE: 511,
                DATA: None
            }
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])

            if RESPONSE in ans and ans[RESPONSE] == 511 and \
                    hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                response = {
                    RESPONSE: 200
                }
                try:
                    send_message(sock, response)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])

                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = {
                    RESPONSE: 400,
                    ERROR: 'Неверный пароль'
                }
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.client_sockets.remove(sock)
                sock.close()

    def service_update_lists(self):
        '''Метод реализующий отправки сервисного сообщения 205 клиентам.'''
        message = {
            RESPONSE: 205
        }
        for client in self.names:
            try:
                send_message(self.names[client], message)
            except OSError:
                self.remove_client(self.names[client])

    def process_message(self, message):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in self.listen_sockets:
            try:
                send_message(self.names[message[DESTINATION]], message)
                logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.listen_sockets:
            logger.error(
                f'Связь с клиентом {message[DESTINATION]} была потеряна. Соединение закрыто, доставка невозможна.')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    def process_client_message(self, message, client_socket):
        logger.debug(f'Разбор сообщения от клиента: {message}')
        if ACTION in message and message[ACTION] == PRESENCE:
            if TIME in message and USER in message:
                self.autorize_user(message, client_socket)

        elif ACTION in message and message[ACTION] == MESSAGE:
            if DESTINATION in message and SENDER in message and TIME in message and MESSAGE_TEXT in message:
                if self.names[message[SENDER]] == client_socket:
                    if message[DESTINATION] in self.names:
                        self.database.process_message(message[SENDER], message[DESTINATION])
                        self.process_message(message)
                        message = {
                            RESPONSE: 200
                        }
                        try:

                            send_message(client_socket, message)
                        except OSError:
                            self.remove_client(client_socket)
                    else:
                        message = {
                            RESPONSE: 400,
                            ERROR: 'Пользователь не зарегистрирован на сервере'
                        }
                        try:
                            send_message(client_socket, message)
                        except OSError:
                            pass
                    return

        elif ACTION in message and message[ACTION] == EXIT:
            if ACCOUNT_NAME in message:
                if self.names[message[ACCOUNT_NAME]] == client_socket:
                    self.remove_client(client_socket)

        elif ACTION in message and message[ACTION] == GET_CONTACTS:
            if USER in message:
                if self.names[message[USER]] == client_socket:
                    message = {
                        RESPONSE: 202,
                        LIST_INFO: self.database.get_contacts(message[USER])
                    }
                    try:
                        send_message(client_socket, message)
                    except OSError:
                        self.remove_client(client_socket)

        elif ACTION in message and message[ACTION] == ADD_CONTACT:
            if ACCOUNT_NAME in message and USER in message:
                if self.names[message[USER]] == client_socket:
                    self.database.add_contact(message[USER], message[ACCOUNT_NAME])
                    message = {
                        RESPONSE: 200,
                    }
                    try:
                        send_message(client_socket, message)
                    except OSError:
                        self.remove_client(client_socket)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT:
            if ACCOUNT_NAME in message and USER in message:
                if self.names[message[USER]] == client_socket:
                    self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
                    message = {
                        RESPONSE: 200,
                    }
                    try:
                        send_message(client_socket, message)
                    except OSError:
                        self.remove_client(client_socket)

        elif ACTION in message and message[ACTION] == USERS_REQUEST:
            if ACCOUNT_NAME in message:
                if self.names[message[ACCOUNT_NAME]] == client_socket:
                    message = {
                        RESPONSE: 202,
                        LIST_INFO: [user[0] for user in self.database.user_list()]
                    }
                    try:
                        send_message(client_socket, message)
                    except OSError:
                        self.remove_client(client_socket)

        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST:
            if ACCOUNT_NAME in message:
                message = {
                    RESPONSE: 511,
                    DATA: self.database.get_pubkey(message[ACCOUNT_NAME])
                }

                if message[DATA]:
                    try:
                        send_message(client_socket, message)
                    except OSError:
                        self.remove_client(client_socket)
                else:
                    message = {
                        RESPONSE: 400,
                        ERROR: 'Нет публичного ключа для данного пользователя'
                    }
                    try:
                        send_message(client_socket, message)
                    except OSError:
                        self.remove_client(client_socket)

        else:
            message = {
                RESPONSE: 400,
                ERROR: 'Запрос некорректен'
            }
            try:
                send_message(client_socket, message)
            except OSError:
                self.remove_client(client_socket)
            return
