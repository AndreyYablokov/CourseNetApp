def ping_site(site_url):
    import chardet
    import subprocess
    import platform

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', site_url]
    command_results = subprocess.Popen(command, stdout=subprocess.PIPE)
    for line in command_results.stdout:
        result = chardet.detect(line)
        line = line.decode(result['encoding']).encode('utf-8')
        print(line.decode('utf-8'))


if __name__ == '__main__':
    urls = ['yandex.ru', 'youtube.com']
    for url in urls:
        ping_site(url)
