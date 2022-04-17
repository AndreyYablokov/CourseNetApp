def write_to_yaml(file, data):
    import yaml

    with open(file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    with open(file, 'r', encoding='utf-8') as f:
        result = yaml.full_load(f)

    if data == result:
        print('Данные успешно записаны и верифицированы')


if __name__ == '__main__':
    file = 'task3_result.yaml'
    init_data = {
        'А': ['Америка', 'Англия'],
        'Б': 2,
        'В': {
            'ВА': 'ВАНЯ',
            'ВЕ': 'ВЕНЬЯМИН'
        }
    }
    write_to_yaml(file, init_data)
