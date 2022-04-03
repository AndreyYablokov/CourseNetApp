import threading
import subprocess
import platform
import ipaddress
import sys


def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', str(host)]
    command_results = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    code = command_results.wait()
    if code == 0:
        print(f'Узел {host} доступен')
    else:
        print(f'Узел {host} не доступен')


def hosts_ping(hosts):
    streams = []
    for host in hosts:
        stream = threading.Thread(target=ping, args=(host, ))
        stream.daemon = True
        stream.start()
        streams.append(stream)

    for stream in streams:
        stream.join()


def host_range_ping(ip_address, count):
    ip_addresses = [ip_address + idx for idx in range(count+1)]
    hosts_ping(ip_addresses)


if __name__ == '__main__':
    ip_address = input('Введите стартовый IP-адрес: ')
    try:
        start_ip_address = ipaddress.ip_address(ip_address)
    except ValueError:
        print('Неверный формат IP-адреса')
        sys.exit(1)
    try:
        count_ip_address = int(input('Введите количество проверяемых IP-адресов (без учета стартового адреса): '))
    except ValueError:
        print('Недопустимый формат ввода количества проверяемых IP-адресов')
        sys.exit(1)
    max_ip_address = ip_address.split('.')
    max_ip_address[3] = '255'
    if start_ip_address + count_ip_address <= ipaddress.ip_address('.'.join(max_ip_address)):
        pass
    else:
        print('Недопустимое количество проверяемых IP-адресов')
        sys.exit(1)

    host_range_ping(start_ip_address, count_ip_address)
