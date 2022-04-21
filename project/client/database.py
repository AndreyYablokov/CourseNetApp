import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class ClientDatabase:
    Base = declarative_base()

    class KnownUsers(Base):
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)

        def __init__(self, login):
            self.login = login

    class MessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        sender = Column(String)
        recipient = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, sender, recipient, message):
            self.sender = sender
            self.recipient = recipient
            self.message = message
            self.date = datetime.now()

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)

        def __init__(self, contact):
            self.login = contact

    def __init__(self, login):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{login}.db3'
        self.engine = create_engine(f'sqlite:///{os.path.join(path, filename)}',
                                    echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(login=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(login=contact).delete()
        self.session.commit()

    def add_users(self, users):
        self.session.query(self.KnownUsers).delete()
        for user in users:
            self.session.add(self.KnownUsers(user))
        self.session.commit()

    def save_message(self, sender, recipient, message):
        self.session.add(self.MessageHistory(sender, recipient, message))
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.login).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.login).all()]

    def check_user(self, login):
        if self.session.query(self.KnownUsers).filter_by(login=login).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(login=contact).count():
            return True
        else:
            return False

    def get_history(self, sender=None, recipient=None):
        query = self.session.query(self.MessageHistory)
        if sender:
            query = query.filter_by(sender=sender)
        if recipient:
            query = query.filter_by(recipient=recipient)
        return [(history_row.sender, history_row.recipient, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for user in ['test3', 'test4', 'test5']:
        test_db.add_contact(user)
    test_db.add_contact('test4')
    test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    test_db.save_message('test1', 'test2',
                         f'Привет! я тестовое сообщение от {datetime.now()}!')
    test_db.save_message('test2', 'test1',
                         f'Привет! я другое тестовое сообщение от {datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('test1'))
    print(test_db.check_user('test10'))
    print(test_db.get_history('test2'))
    print(test_db.get_history(recipient='test2'))
    print(test_db.get_history('test3'))
    test_db.del_contact('test4')
    print(test_db.get_contacts())
