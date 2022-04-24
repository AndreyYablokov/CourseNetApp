import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QTimer
from server.stat_window import HistoryWindow
from server.config_window import ConfigWindow
from server.add_user import RegisterUser
from server.remove_user import DelUserDialog


# Класс основного окна
class MainWindow(QMainWindow):
    def __init__(self, database, server, config):
        super().__init__()

        self.database = database
        self.server_thread = server
        self.config = config

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

        # Кнопка регистрации пользователя
        self.register_btn = QAction('Регистрация пользователя', self)

        # Кнопка удаления пользователя
        self.remove_btn = QAction('Удаление пользователя', self)

        # Статусбар
        self.statusBar()
        self.statusBar().showMessage('Server Working')

        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exit_button)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)

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

        # Таймер, обновляющий список клиентов 1 раз в секунду
        self.timer = QTimer()
        self.timer.timeout.connect(self.gui_create_model_active_users)
        self.timer.start(1000)

        self.refresh_button.triggered.connect(self.gui_create_model_active_users)
        self.show_history_button.triggered.connect(self.gui_create_model_history)
        self.config_button.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)

        self.show()

    # Функция создания таблицы для отображения активных пользователей
    def gui_create_model_active_users(self):
        active_users = self.database.active_user_list()
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
        self.active_users_table.setModel(active_users_table)
        self.active_users_table.resizeColumnsToContents()
        self.active_users_table.resizeColumnsToContents()

    # Функция заполнения таблицы историей сообщений
    def gui_create_model_history(self):
        global stat_window
        stat_window = HistoryWindow(self.database)
        stat_window.show()

    def server_config(self):
        '''Метод создающий окно с настройками сервера.'''
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        '''Метод создающий окно регистрации пользователя.'''
        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):
        '''Метод создающий окно удаления пользователя.'''
        global rem_window
        rem_window = DelUserDialog(self.database, self.server_thread)
        rem_window.show()
