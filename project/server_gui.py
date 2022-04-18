import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


# Функция создания таблицы для отображения активных пользователей
def gui_create_model_active_users(database):
    active_users = database.active_user_list()
    active_users_table = QStandardItemModel()
    active_users_table.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
    for active_user in active_users:
        user = QStandardItem(active_user[0])
        user.setEditable(False)
        ip = QStandardItem(active_user[1])
        ip.setEditable(False)
        port = QStandardItem(str(active_user[2]))
        port.setEditable(False)
        time = QStandardItem(str(active_user[3].replace(microsecond=0)))
        time.setEditable(False)
        active_users_table.appendRow([user, ip, port, time])
    return active_users_table


# Функция заполнения таблицы историей сообщений
def gui_create_model_history(database):
    messages = database.message_history()
    history_table = QStandardItemModel()
    history_table.setHorizontalHeaderLabels(
        ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
    for message in messages:
        user = QStandardItem(message[0])
        user.setEditable(False)
        last_seen = QStandardItem(str(message[1].replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(message[2]))
        sent.setEditable(False)
        recvd = QStandardItem(str(message[3]))
        recvd.setEditable(False)
        history_table.appendRow([user, last_seen, sent, recvd])
    return history_table


# Класс основного окна
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Кнопка выхода
        self.exit_button = QAction('Выйти', self)
        self.exit_button.setShortcut('Ctrl+Q')
        self.exit_button.triggered.connect(qApp.quit)

        # Кнопка обновить список клиентов
        self.refresh_button = QAction('Обновить список', self)
        self.refresh_button.setShortcut('Ctrl+R')

        # Кнопка вывести историю сообщений
        self.show_history_button = QAction('История клиентов', self)
        self.show_history_button.setShortcut('Ctrl+H')

        # Кнопка настроек сервера
        self.config_button = QAction('Настройки сервера', self)
        self.config_button.setShortcut('Ctrl+S')

        # Статусбар
        self.statusBar()

        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exit_button)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)

        # Настройки основного окна
        self.setFixedSize(800, 600)
        self.setWindowTitle('Сервер')

        # Надпись о том, что ниже список подключённых клиентов
        self.active_users_label = QLabel('Список подключённых клиентов:', self)
        self.active_users_label.setFixedSize(400, 15)
        self.active_users_label.move(10, 35)

        # Окно со списком подключённых клиентов
        self.active_users_table = QTableView(self)
        self.active_users_table.move(10, 55)
        self.active_users_table.setFixedSize(780, 400)

        self.show()


# Класс окна с историей пользователей
class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(680, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(290, 650)
        self.close_button.clicked.connect(self.close)

        # Таблица истории пользователей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(658, 620)

        self.show()


# Класс окна настроек
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setFixedSize(375, 260)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # Строка с путём базы данных
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути к базе данных
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(275, 28)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(165, 20)

        # Метка с номером порта
        self.port_label = QLabel('Номер порта для соединений: ', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(165, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel('IP адрес для соединений: ', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Метка с напоминанием о пустом поле
        self.ip_label_note = QLabel('Примечание. Оставьте это поле пустым, чтобы принимать\nсоединения с любых адресов.', self)
        self.ip_label_note.move(10, 175)
        self.ip_label_note.setFixedSize(500, 30)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(165, 20)

        # Кнопка сохранения настроек
        self.save_button = QPushButton('Сохранить', self)
        self.save_button.move(190, 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # main_window = MainWindow()
    # main_window.statusBar().showMessage('Тест строки состояния')
    # test_list = QStandardItemModel(main_window)
    # test_list.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
    # test_list.appendRow(
    #     [QStandardItem('test1'), QStandardItem('192.198.0.5'), QStandardItem('23544'), QStandardItem('16:20:34')])
    # test_list.appendRow(
    #     [QStandardItem('test2'), QStandardItem('192.198.0.8'), QStandardItem('33245'), QStandardItem('16:22:11')])
    # main_window.active_users_table.setModel(test_list)
    # main_window.active_users_table.resizeColumnsToContents()
    # app.exec_()

    # ----------------------------------------------------------
    # app = QApplication(sys.argv)
    # window = HistoryWindow()
    # test_list = QStandardItemModel(window)
    # test_list.setHorizontalHeaderLabels(
    #     ['Имя клиента', 'Последнее посещение', 'Отправлено', 'Получено'])
    # test_list.appendRow(
    #     [QStandardItem('test1'), QStandardItem('Fri Dec 12 16:20:34 2020'), QStandardItem('2'), QStandardItem('3')])
    # test_list.appendRow(
    #     [QStandardItem('test2'), QStandardItem('Fri Dec 12 16:23:12 2020'), QStandardItem('8'), QStandardItem('5')])
    # window.history_table.setModel(test_list)
    # window.history_table.resizeColumnsToContents()
    #
    # app.exec_()

    # ----------------------------------------------------------
    app = QApplication(sys.argv)
    dial = ConfigWindow()

    app.exec_()
