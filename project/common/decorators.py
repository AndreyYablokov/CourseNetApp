import logging
import socket

import log.client_log_config
import log.server_log_config
import sys
import traceback
from functools import wraps

if sys.argv[0].find('client_main.py') == -1:
    logger = logging.getLogger('server_logger')
else:
    logger = logging.getLogger('client_logger')


def log(func_to_log):
    """
    Декоратор для логирования вызова функции
    """
    @wraps(func_to_log)
    def wrap(*args, **kwargs):
        result = func_to_log(*args, **kwargs)
        logger.debug(f'Была вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}.'
                     f'Функция вызвана из модуля {func_to_log.__module__}.'
                     f'Функция вызвана из функции {traceback.format_stack()[0].strip().split()[-1]}')
        return result
    return wrap

def login_required(func):
    """
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    """

    def checker(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр MessageProcessor
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from server.core import MessageProcessor
        from common.constants import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение. Если presence, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker

