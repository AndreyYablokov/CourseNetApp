import logging
import time
from logging import handlers
import os

server_logger = logging.getLogger('server_logger')

server_log_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(module)-10s %(message)s")

path_to_log_dir = os.path.dirname(os.path.abspath(__file__))
path_to_log_file_handler = os.path.join(path_to_log_dir, 'server.log')
path_to_log_timed_rotating_file_handler = os.path.join(path_to_log_dir, 'server_timed_rotating.log')
server_file_handler = logging.FileHandler(path_to_log_file_handler, encoding='utf-8')
server_file_handler.setLevel(logging.DEBUG)
server_file_handler.setFormatter(server_log_formatter)

server_timed_rotating_file_handler = handlers.TimedRotatingFileHandler(
    path_to_log_timed_rotating_file_handler, interval=1, when='D', encoding='utf-8')
server_timed_rotating_file_handler.setLevel(logging.DEBUG)
server_timed_rotating_file_handler.setFormatter(server_log_formatter)

server_logger.addHandler(server_file_handler)
server_logger.addHandler(server_timed_rotating_file_handler)
server_logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    server_logger.debug('Тестирование добавления сообщения уровня DEBUG')
    server_logger.info('Тестирование добавления сообщения уровня INFO')
    server_logger.warning('Тестирование добавления сообщения уровня WARNING')
    server_logger.error('Тестирование добавления сообщения уровня ERROR')
    server_logger.critical('Тестирование добавления сообщения уровня CRITICAL')
