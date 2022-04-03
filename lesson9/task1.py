import threading
import subprocess
import platform
import ipaddress


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


if __name__ == '__main__':
    hosts = ['yandex.ru',
             'google.com',
             ipaddress.ip_address('127.0.0.1'),
             ipaddress.ip_address('192.168.0.5'),
             ipaddress.ip_address('192.168.0.10'),
             ipaddress.ip_address('192.168.0.15'),
             ]
    hosts_ping(hosts)
