"""Программа-лаунчер"""


if __name__ == '__main__':

    import subprocess

    PROCESSES = []

    while True:
        ACTION = input('Выберите действие: q - выход, '
                       's - запустить сервер и клиенты, '
                       'x - закрыть все окна: ')

        if ACTION == 'q':
            break
        elif ACTION == 's':
            clients_count = int(input('Введите количество клиентов для запуска: '))
            # PROCESSES.append(subprocess.Popen('python server_main.py',
            #                                   creationflags=subprocess.CREATE_NEW_CONSOLE))
            for client_num in range(1, clients_count+1):
                PROCESSES.append(subprocess.Popen(['python', 'client_main.py', '-n', f'test{client_num}'],
                                                  creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif ACTION == 'x':
            while PROCESSES:
                VICTIM = PROCESSES.pop()
                VICTIM.kill()
