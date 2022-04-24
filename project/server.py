import argparse
import os.path
import select
import socket
import sys
import logging
from common.constants import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT, LIST_INFO, ADD_CONTACT, REMOVE_CONTACT, \
    GET_CONTACTS, USERS_REQUEST
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import ListenPort
from common.metaclasses import ServerVerifier
from server.core import MessageProcessor
from server.main_window import MainWindow
from server.database import ServerDatabase
import threading
import configparser
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt

logger = logging.getLogger('server_logger')


@log
def get_command_line_params(default_port, default_address):
    logger.debug(
        f'Инициализация парсера аргументов коммандной строки: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    logger.debug('Аргументы успешно загружены.')

    return {
        'listen_port': listen_port,
        'listen_address': listen_address,
        'gui_flag': gui_flag,
    }


@log
def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


if __name__ == '__main__':
    config = config_load()

    command_line_params = get_command_line_params(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])
    listen_address = command_line_params['listen_address']
    listen_port = command_line_params['listen_port']
    gui_flag = command_line_params['gui_flag']

    server_database = ServerDatabase(
        os.path.join(config['SETTINGS']['Database_path'],
                     config['SETTINGS']['Database_file'])
    )

    server = MessageProcessor(listen_address, listen_port, server_database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                server.running = False
                server.join()
                break

    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(server_database, server, config)
        server_app.exec_()

        server.running = False
