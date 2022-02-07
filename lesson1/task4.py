def convert_str_to_bytes(variables):
    return list(map(lambda variable: variable.encode('utf-8'), variables))


def convert_bytes_to_str(variables):
    return list(map(lambda variable: variable.decode('utf-8'), variables))


if __name__ == '__main__':
    from task2 import print_variables_info

    words_in_str_format = ['разработка', 'администрирование', 'protocol', 'standard']
    word_in_bytes_type = convert_str_to_bytes(words_in_str_format)
    print_variables_info(word_in_bytes_type)
    word_in_str_type = convert_bytes_to_str(word_in_bytes_type)
    print_variables_info(word_in_str_type)
