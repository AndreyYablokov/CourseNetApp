import logging
import log.client_log_config
import log.server_log_config
import sys
import traceback
from functools import wraps

if sys.argv[0].find('client.py') == -1:
    logger = logging.getLogger('server_logger')
else:
    logger = logging.getLogger('client_logger')


def log(func_to_log):
    @wraps(func_to_log)
    def wrap(*args, **kwargs):
        result = func_to_log(*args, **kwargs)
        logger.debug(f'Была вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}.'
                     f'Функция вызвана из модуля {func_to_log.__module__}.'
                     f'Функция вызвана из функции {traceback.format_stack()[0].strip().split()[-1]}')
        return result
    return wrap

