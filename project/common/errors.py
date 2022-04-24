class IncorrectDataRecivedError(Exception):
    """Указывает на получение некоректных данных"""

    def __str__(self):
        return 'Принято некоректное сообщение от удаленного устройства'


class NonDictInputError(Exception):
    """Указывает на то, что получен не словарь"""

    def __str__(self):
        return 'Аргумент функции должен быть словарем'


class ReqFieldMissingError(Exception):
    """Указывает на отсутствие обязательного поля в принятом словаре"""

    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}'


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
