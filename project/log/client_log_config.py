import logging
import os

client_logger = logging.getLogger('client_logger')

client_log_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(module)-10s %(message)s")

path_to_log_dir = os.path.dirname(os.path.abspath(__file__))
path_to_log = os.path.join(path_to_log_dir, 'client.log')
client_file_handler = logging.FileHandler(path_to_log, encoding='utf-8')
client_file_handler.setLevel(logging.DEBUG)
client_file_handler.setFormatter(client_log_formatter)

client_logger.addHandler(client_file_handler)
client_logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    client_logger.debug('Тестирование добавления сообщения уровня DEBUG')
    client_logger.info('Тестирование добавления сообщения уровня INFO')
    client_logger.warning('Тестирование добавления сообщения уровня WARNING')
    client_logger.error('Тестирование добавления сообщения уровня ERROR')
    client_logger.critical('Тестирование добавления сообщения уровня CRITICAL')
