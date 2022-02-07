def print_variables_type(variables):
    print('-' * 150)
    for variable in variables:
        print(f'Variable content: {variable}, variable type: {type(variable)}')


if __name__ == '__main__':
    words_in_str_format = ['разработка', 'сокет', 'декоратор']
    print_variables_type(words_in_str_format)
    words_in_unicode = [
        '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
        '\u0441\u043e\u043a\u0435\u0442',
        '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
    ]
    print_variables_type(words_in_unicode)
