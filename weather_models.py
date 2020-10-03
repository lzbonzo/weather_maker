import peewee
import os
from playhouse.db_url import connect

DATABASE = peewee.SqliteDatabase('weather.db')


class BaseTable(peewee.Model):

    class Meta:
        database = DATABASE


class DayWeather(BaseTable):
    date = peewee.DateField()
    date_for_user = peewee.CharField()
    day_part = peewee.CharField()
    condition = peewee.CharField()
    temp = peewee.CharField()
    pressure = peewee.CharField()
    humidity = peewee.CharField()
    wind_speed = peewee.CharField()
    wind_direction = peewee.CharField()
    feels_like = peewee.CharField()
    day_name = peewee.CharField()


db = connect(os.environ.get('DATABASE') or 'sqlite:///weather.db')
