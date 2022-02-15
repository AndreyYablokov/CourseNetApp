import json
from common.constants import MAX_MESSAGE_LENGTH, ENCODING


def get_message(socket):
    """
    Принять и декодировать сообщение
    :param socket:
    :return:
    """

    encoded_message = socket.recv(MAX_MESSAGE_LENGTH)
    if isinstance(encoded_message, bytes):
        decoded_message = encoded_message.decode(ENCODING)
        message = json.loads(decoded_message)
        if isinstance(message, dict):
            return message
        raise ValueError
    raise ValueError


def send_message(socket, message):
    """
    Закодировать и отправить сообщение
    :param socket:
    :param message:
    :return:
    """

    if isinstance(message, dict):
        decoded_message = json.dumps(message)
        encoded_message = decoded_message.encode(ENCODING)
        socket.send(encoded_message)
    else:
        raise ValueError

