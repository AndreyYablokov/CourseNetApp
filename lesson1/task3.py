def check_conversion_to_bytes(variables):
    failed_vars = []
    for variable in variables:
        try:
            eval(f"b'{variable}'")
        except SyntaxError:
            failed_vars.append(variable)

    if failed_vars:
        for failed_var in failed_vars:
            print(f'Word "{failed_var}" cannot be written in byte type')
        return False

    print('All words can be written in byte type')
    return True


if __name__ == '__main__':
    words_in_str_format = ['attribute', 'класс', 'функция', 'type']
    check_conversion_to_bytes(words_in_str_format)
