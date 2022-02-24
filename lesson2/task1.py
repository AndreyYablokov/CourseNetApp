def detect_file_encodings(file):
    from chardet import detect
    with open(file, 'rb') as f:
        content = f.read()
    return detect(content)['encoding']


def get_data(files):
    import re

    params_name = ['Изготовитель ОС', 'Название ОС', 'Код продукта', 'Тип системы']
    params_list = ['os_prod', 'os_name', 'os_code', 'os_type']
    os_prod = []
    os_name = []
    os_code = []
    os_type = []
    result = [params_name]

    for file in files:
        encoding = detect_file_encodings(file)
        with open(file, 'r', encoding=encoding) as f:
            for line in f:
                for param_name, param_list in zip(params_name, params_list):
                    match = re.search(fr'^{param_name}:\s+(.+)$', line.strip())
                    if match:
                        eval(f'{param_list}.append("{match.group(1)}")')

    for os_prod_val, os_name_val, os_code_val, os_type_val in zip(os_prod, os_name, os_code, os_type):
        result.append([os_prod_val, os_name_val, os_code_val, os_type_val])

    return result


def write_to_csv(input_files, output_file):
    import csv

    data = get_data(input_files)
    with open(output_file, 'w', encoding='utf-8') as f:
        csv.writer(f, quoting=csv.QUOTE_NONNUMERIC).writerows(data)


if __name__ == '__main__':
    files_name = [f'info_{idx}.txt' for idx in range(1, 4)]
    output_file = 'task1_result.csv'
    write_to_csv(files_name, output_file)

