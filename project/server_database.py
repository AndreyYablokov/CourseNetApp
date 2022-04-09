from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class ServerDatabase:
    Base = declarative_base()

    class Users(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_connection = Column(DateTime)

        def __init__(self, login):
            self.login = login
            self.last_connection = datetime.now()

    class ActiveUsers(Base):
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('users.id'), unique=True)
        ip_address = Column(String)
        port = Column(Integer)
        connection_datetime = Column(DateTime)

        def __init__(self, user, ip_address, port, connection_datetime):
            self.user = user
            self.ip_address = ip_address
            self.port = port
            self.connection_datetime = connection_datetime

    class LoginHistory(Base):
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('users.id'))
        ip_address = Column(String)
        port = Column(Integer)
        connection_datetime = Column(DateTime)

        def __init__(self, user, ip_address, port, connection_datetime):
            self.user = user
            self.ip_address = ip_address
            self.port = port
            self.connection_datetime = connection_datetime

    def __init__(self):
        self.engine = create_engine('sqlite:///server_db.db3', echo=False, pool_recycle=7200)

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, login, ip_address, port):
        query_result = self.session.query(self.Users).filter_by(login=login)
        if query_result.count():
            user = query_result.first()
            user.last_connection = datetime.now()
        else:
            user = self.Users(login)
            self.session.add(user)
            self.session.commit()

        self.session.add(self.ActiveUsers(user.id, ip_address, port, datetime.now()))
        self.session.add(self.LoginHistory(user.id, ip_address, port, datetime.now()))
        self.session.commit()

    def user_logout(self, login):
        user = self.session.query(self.Users).filter_by(login=login).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def user_list(self):
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
        query_result = self.session.query(self.Users.login,
                                          self.LoginHistory.ip_address,
                                          self.LoginHistory.port,
                                          self.LoginHistory.connection_datetime
                                          ).join(self.Users)
        if login:
            query_result = query_result.filter(self.Users.login == login)
        return query_result.all()


if __name__ == '__main__':
    database = ServerDatabase()
    database.user_login('test_client_1', '192.168.0.2', 1025)
    database.user_login('test_client_2', '192.168.0.3', 1026)
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
