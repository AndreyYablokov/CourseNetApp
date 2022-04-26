from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class ServerDatabase:
    """Класс базы данных сервера"""
    Base = declarative_base()

    class Users(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_connection = Column(DateTime)
        passwd_hash = Column(String)
        pubkey = Column(Text)

        def __init__(self, login, passwd_hash):
            self.login = login
            self.last_connection = datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None
            self.id = None

    class ActiveUsers(Base):
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'), unique=True)
        ip_address = Column(String)
        port = Column(Integer)
        connection_datetime = Column(DateTime)

        def __init__(self, user, ip_address, port, connection_datetime):
            self.user = user
            self.ip_address = ip_address
            self.port = port
            self.connection_datetime = connection_datetime
            self.id = None

    class LoginHistory(Base):
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        ip_address = Column(String)
        port = Column(Integer)
        connection_datetime = Column(DateTime)

        def __init__(self, user, ip_address, port, connection_datetime):
            self.user = user
            self.ip_address = ip_address
            self.port = port
            self.connection_datetime = connection_datetime
            self.id = None

    class UsersContacts(Base):
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        contact = Column(ForeignKey('users.id'))

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory(Base):
        __tablename__ = 'users_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self,path):
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, login, ip_address, port, key):
        """Метод входа пользователя"""
        query_result = self.session.query(self.Users).filter_by(login=login)
        if query_result.count():
            user = query_result.first()
            user.last_connection = datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        self.session.add(self.ActiveUsers(user.id, ip_address, port, datetime.now()))
        self.session.add(self.LoginHistory(user.id, ip_address, port, datetime.now()))
        self.session.commit()

    def user_logout(self, login):
        """Метод выхода пользователя"""
        user = self.session.query(self.Users).filter_by(login=login).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(login=name).delete()
        self.session.commit()

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.pubkey

    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.Users).filter_by(login=name).count():
            return True
        else:
            return False

    def process_message(self, sender, recipient):
        """Метод обработки сообщения"""
        sender = self.session.query(self.Users).filter_by(login=sender).first()
        recipient = self.session.query(self.Users).filter_by(login=recipient).first()
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender.id).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient.id).first()
        recipient_row.accepted += 1
        self.session.commit()

    def add_contact(self, login_user, login_contact):
        """Метод добавления контакта"""
        # Получаем ID пользователей
        user = self.session.query(self.Users).filter_by(login=login_user).first()
        contact = self.session.query(self.Users).filter_by(login=login_contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        self.session.add(self.UsersContacts(user.id, contact.id))
        self.session.commit()

    def remove_contact(self, login_user, login_contact):
        """Метод удаления контакта"""
        # Получаем ID пользователей
        user = self.session.query(self.Users).filter_by(login=login_user).first()
        contact = self.session.query(self.Users).filter_by(login=login_contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # Удаляем требуемое
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def user_list(self):
        """Метод получения списка пользователей"""
        query_result = self.session.query(self.Users.login,
                                          self.Users.last_connection)
        return query_result.all()

    def active_user_list(self):
        query_result = self.session.query(self.Users.login,
                                          self.ActiveUsers.ip_address,
                                          self.ActiveUsers.port,
                                          self.ActiveUsers.connection_datetime
                                          ).join(self.Users)
        return query_result.all()

    def login_history_list(self, login=None):
        """Метод получения списка истории"""
        query_result = self.session.query(self.Users.login,
                                          self.LoginHistory.ip_address,
                                          self.LoginHistory.port,
                                          self.LoginHistory.connection_datetime
                                          ).join(self.Users)
        if login:
            query_result = query_result.filter(self.Users.login == login)
        return query_result.all()

    def get_contacts(self, login):
        """Метод получения списка контактов"""
        # Запрашиваем указанного пользователя
        user = self.session.query(self.Users).filter_by(login=login).one()

        # Запрашиваем его список контактов
        query = self.session.query(self.UsersContacts, self.Users.login). \
            filter_by(user=user.id). \
            join(self.Users, self.UsersContacts.contact == self.Users.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    def message_history(self):
        """Метод получения истории сообщений"""
        query = self.session.query(
            self.Users.login,
            self.Users.last_connection,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.Users)
        # Возвращаем список кортежей
        return query.all()


if __name__ == '__main__':
    database = ServerDatabase('server_db.db3')
    database.user_login('test_client_1', '192.168.0.2', 1025)
    database.user_login('test_client_2', '192.168.0.3', 1026)
    database.user_login('test_client_3', '192.168.0.4', 1027)
    database.user_login('test_client_4', '192.168.0.5', 1028)
    print('-' * 150)
    print('Исходные данные в БД')
    print('Пользователи:')
    print(database.user_list())
    print('Активные пользователи:')
    print(database.active_user_list())

    print('-'*150)
    print('Данные в БД после выхода первого пользователя')
    database.user_logout('test_client_1')
    print('Пользователи:')
    print(database.user_list())
    print('Активные пользователи:')
    print(database.active_user_list())
    print('История входов:')
    print(database.login_history_list())

    print('-'*150)
    print('Данные в БД после выхода второго пользователя')
    database.user_logout('test_client_2')
    print('Пользователи:')
    print(database.user_list())
    print('Активные пользователи:')
    print(database.active_user_list())
    print('История входов:')
    print(database.login_history_list())
    print('История входов первого пользователя:')
    print(database.login_history_list('test_client_1'))

    print('-'*150)
    print('Данные после обмена сообщениями между мользователями')
    database.add_contact('test_client_1', 'test_client_2')
    database.add_contact('test_client_2', 'test_client_3')
    database.add_contact('test_client_3', 'test_client_4')
    database.remove_contact('test_client_1', 'test_client_2')
    database.process_message('test_client_2', 'test_client_3')
    print(database.message_history())
