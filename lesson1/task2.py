def print_variables_info(variables):
    print('-' * 150)
    for variable in variables:
        print(f'Variable content: {variable}, '
              f'variable type: {type(variable)}, '
              f'variable length: {len(variable)}')


def convert_str_to_bytes(variables):
    result = []
    for variable in variables:
        variable_in_bytes = eval(f"b'{variable}'")
        result.append(variable_in_bytes)
    return result


if __name__ == '__main__':
    words_in_str_format = ['class', 'function', 'method']
    print_variables_info(words_in_str_format)
    words_in_bytes_type = convert_str_to_bytes(words_in_str_format)
    print_variables_info(words_in_bytes_type)
