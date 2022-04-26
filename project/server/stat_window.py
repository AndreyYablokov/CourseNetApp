import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class HistoryWindow(QDialog):
    """Класс окна с историей пользователей"""
    def __init__(self, database):
        super().__init__()
        self.database = database
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

    def create_stat_model(self):
        '''Метод реализующий заполнение таблицы статистикой сообщений.'''
        # Список записей из базы
        stat_list = self.database.message_history()

        # Объект модели данных:
        data_list = QStandardItemModel()
        data_list.setHorizontalHeaderLabels(
            ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
        for row in stat_list:
            user, last_seen, sent, recvd = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            recvd = QStandardItem(str(recvd))
            recvd.setEditable(False)
            data_list.appendRow([user, last_seen, sent, recvd])
        self.stat_table.setModel(list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()

