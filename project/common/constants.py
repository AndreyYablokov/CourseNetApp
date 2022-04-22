import logging

# Константы для сетевого взаимодействия
DEFAULT_PORT = 7777
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_MESSAGE_LENGTH = 1024
ENCODING = 'utf-8'
LOGGING_LEVEL = logging.DEBUG
SERVER_CONFIG = 'server_dist.ini'


# Констатнты протокола JIM
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
STATUS = 'status'
TYPE = 'type'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
SENDER = 'sender'
DESTINATION = 'destination'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove_contact'
ADD_CONTACT = 'add_contact'
USERS_REQUEST = 'get_users'
EXIT = 'exit'
