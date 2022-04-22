import dis


class ServerVerifier(type):
    def __init__(cls, cls_name, cls_parents, cls_dict):
        ordinary_functions = []
        functions_with_decorators = []
        arguments = []
        for key in cls_dict:
            try:
                instructions = dis.get_instructions(cls_dict[key])
            except TypeError:
                pass
            else:
                for instruction in instructions:
                    if instruction.opname == 'LOAD_GLOBAL':
                        if instruction.argval not in ordinary_functions:
                            ordinary_functions.append(instruction.argval)
                    elif instruction.opname == 'LOAD_METHOD':
                        if instruction.argval not in functions_with_decorators:
                            functions_with_decorators.append(instruction.argval)
                    elif instruction.opname == 'LOAD_ATTR':
                        if instruction.argval not in arguments:
                            arguments.append(instruction.argval)
        if 'connect' in ordinary_functions or 'connect' in functions_with_decorators:
            raise TypeError('Использование метода connect не допустимо в классе сервера')
        if not ('SOCK_STREAM' in arguments and 'AF_INET' in arguments):
            raise ValueError('Некоректная инициализация сокета')
        super().__init__(cls_name, cls_parents, cls_dict)


class ClientVerifier(type):
    def __init__(cls, cls_name, cls_parents, cls_dict):
        ordinary_functions = []
        functions_with_decorators = []
        arguments = []
        for key in cls_dict:
            try:
                instructions = dis.get_instructions(cls_dict[key])
            except TypeError:
                pass
            else:
                for instruction in instructions:
                    if instruction.opname == 'LOAD_GLOBAL':
                        if instruction.argval not in ordinary_functions:
                            ordinary_functions.append(instruction.argval)
                    elif instruction.opname == 'LOAD_METHOD':
                        if instruction.argval not in functions_with_decorators:
                            functions_with_decorators.append(instruction.argval)
                    elif instruction.opname == 'LOAD_ATTR':
                        if instruction.argval not in arguments:
                            arguments.append(instruction.argval)
        if 'accept' in ordinary_functions or 'listen' in ordinary_functions \
                or 'accept' in functions_with_decorators or 'listen' in functions_with_decorators:
            raise TypeError('Использование методов listen и accept не допустимо в классе клиента')
        if 'get_message' in ordinary_functions or 'send_message' in ordinary_functions:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(cls_name, cls_parents, cls_dict)
