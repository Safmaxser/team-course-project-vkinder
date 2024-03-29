import sqlalchemy as sq
from sqlalchemy import and_
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id_vk = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(length=100))
    last_name = sq.Column(sq.String(length=100))
    favorites = relationship('Favorites', cascade="all, delete",
                             backref="users")
    blacklist = relationship('Blacklist', cascade="all, delete",
                             backref="users")


class Favorites(Base):
    __tablename__ = 'favorites'
    id_vk_person = sq.Column(sq.BIGINT, primary_key=True)
    id_vk_user = sq.Column(sq.Integer, sq.ForeignKey('users.id_vk'),
                           primary_key=True)

    def __repr__(self):
        return (f'{self.__class__.__name__}({self.id_vk_person!r}, '
                f'{self.id_vk_user!r})')


class Blacklist(Base):
    __tablename__ = 'blacklist'
    id_vk_person = sq.Column(sq.BIGINT, primary_key=True)
    id_vk_user = sq.Column(sq.Integer, sq.ForeignKey('users.id_vk'),
                           primary_key=True)


def create_tables_models(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


class OperationsDB:
    def __init__(self, drive, database, connect_name, port, user, password):
        self.drive = drive
        self.database = database
        self.connect_name = connect_name
        self.port = port
        self.user = user
        self.password = password
        self.engine = None
        self.session = None

    def __enter__(self):
        self.connect()
        self.create_tables()
        self.open_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def connect(self):
        dsn = (f'{self.drive}://{self.user}:{self.password}@'
               f'{self.connect_name}:{self.port}/{self.database}')
        self.engine = sq.create_engine(dsn, pool_pre_ping=True)

    def create_tables(self):
        create_tables_models(self.engine)

    def open_session(self):
        session = sessionmaker(bind=self.engine)
        self.session = session()

    def close_session(self):
        self.session.close()

    def exists_user(self, key_id):
        user = self.session.query(Users).get(key_id)
        if user:
            return True
        else:
            return False

    def add_user(self, **user_data):
        with self.session as sn:
            try:
                user = Users(**user_data)
                sn.add(user)
                sn.commit()
            except sq.exc.IntegrityError:
                pass

    def exists_blacklist(self, id_vk_user, id_vk_person):
        with self.session as sn:
            blacklist = sn.query(Blacklist)
            blacklist = blacklist.filter(
                (Blacklist.id_vk_user == id_vk_user) &
                (Blacklist.id_vk_person == id_vk_person)).first()
        if blacklist:
            return True
        else:
            return False

    def del_favorites(self, id_vk_user, id_vk_person):
        with self.session as sn:
            favorites = sn.query(Favorites)
            favorites = favorites.filter(
                and_(Favorites.id_vk_user == id_vk_user,
                     Favorites.id_vk_person == id_vk_person)).first()
            if favorites:
                sn.delete(favorites)
                sn.commit()
            else:
                pass

    def del_blacklist(self, id_vk_user, id_vk_person):
        with self.session as sn:
            blacklist = sn.query(Blacklist)
            blacklist = blacklist.filter(
                (Blacklist.id_vk_user == id_vk_user) &
                (Blacklist.id_vk_person == id_vk_person)).first()
            if blacklist:
                sn.delete(blacklist)
                sn.commit()
            else:
                pass

    def add_favorites(self, id_vk_user, id_vk_person):
        self.del_blacklist(id_vk_user, id_vk_person)
        if id_vk_user and id_vk_person:
            with self.session as sn:
                try:
                    user = Favorites(id_vk_user=id_vk_user,
                                     id_vk_person=id_vk_person)
                    sn.add(user)
                    sn.commit()
                except sq.exc.IntegrityError:
                    pass

    def add_blacklist(self, id_vk_user, id_vk_person):
        self.del_favorites(id_vk_user, id_vk_person)
        if id_vk_user and id_vk_person:
            with self.session as sn:
                try:
                    user = Blacklist(id_vk_user=id_vk_user,
                                     id_vk_person=id_vk_person)
                    sn.add(user)
                    sn.commit()
                except sq.exc.IntegrityError:
                    pass

    def get_favorites(self, id_user):
        sql_query = self.session.query(Favorites.id_vk_person)
        return sql_query.filter(Favorites.id_vk_user == id_user).all()

    def get_blacklist(self, id_user):
        sql_query = self.session.query(Blacklist.id_vk_person)
        return sql_query.filter(Blacklist.id_vk_user == id_user).all()
