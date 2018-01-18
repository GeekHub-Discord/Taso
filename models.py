import config
from peewee import *
import pymysql
from playhouse.shortcuts import RetryOperationalError

cfg = config.botConfig()

class MySQLDB(RetryOperationalError, MySQLDatabase):
    pass

class SqliteDB(SqliteDatabase):
    pass

if cfg.dbtype == 'sqlite':
    my_db = SqliteDB(f'{cfg.database}.db')
else:
    my_db = MySQLDB(
            cfg.database,
            host=cfg.dbhost,
            port=3306,
            user=cfg.dbuser,
            password=cfg.dbpasswd,
            charset='utf8mb4')


class BaseModel(Model):
    class Meta:
        database = my_db


class Server(BaseModel):
    sid = BigIntegerField(null=False, primary_key=True)
    announce_channel = BigIntegerField(null=True)
    experience = BigIntegerField(null=False, default=0)
    level = IntegerField(null=False, default=1)


class User(BaseModel):
    uid = BigIntegerField(null=False, primary_key=True)
    experience = BigIntegerField(null=False, default=0)
    level = IntegerField(null=False, default=1)


class LocalLevel(BaseModel):
    user = ForeignKeyField(User)
    server = ForeignKeyField(Server)
    experience = BigIntegerField(null=False, default=0)
    level = IntegerField(null=False, default=1)


class Role(BaseModel):
    rid = BigIntegerField(null=False, primary_key=True)
    awardlevel = IntegerField(null=True)
    assignable = BooleanField(null=False, default=False)
    server = ForeignKeyField(Server)


my_db.create_tables([Server, User, LocalLevel, Role], safe=True)
