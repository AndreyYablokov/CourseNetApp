import logging
logger = logging.getLogger('server_logger')


class ListenPort:
    """ Дескриптор порта сервера """
    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            logger.critical('Попытка запуска сервера с неверным номером порта. '
                            'Номер порта должен быть из диапазона [1024;65535]')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
