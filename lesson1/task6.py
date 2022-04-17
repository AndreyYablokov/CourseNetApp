def create_file(file_name, file_content):
    with open(file_name, 'w', encoding='utf-8') as f:
        for elem in file_content:
            f.write(f'{elem}\n')


def detect_file_encodings(file_name):
    from chardet import detect
    with open(file_name, 'rb') as f:
        content = f.read()
    return detect(content)['encoding']


def print_file(file_name, encoding):
    with open(file_name, 'r', encoding=encoding) as f:
        for line in f:
            print(line.strip())


if __name__ == '__main__':
    file_name = 'test_file.txt'
    file_content = ['сетевое программирование', 'сокет', 'декоратор']
    create_file(file_name, file_content)
    encoding = detect_file_encodings(file_name)
    print_file(file_name, encoding)
