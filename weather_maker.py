import numpy
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import cv2
from PIL import ImageFont, ImageDraw, Image
from weather_models import DayWeather
import peewee
import datetime
import math


class WeatherMaker:

    def __init__(self):
        self.days = []
        self.weather = OrderedDict()
        self.list_of_days = []

    def make_weather_for_day_range(self, days_range):
        """ Собираем данные с yandex"""
        yandex_weather = requests.get('https://yandex.ru/pogoda/moscow/details')
        if yandex_weather.status_code == 200:
            html_doc = BeautifulSoup(yandex_weather.text, features='html.parser')
            self.list_of_days = html_doc.find_all('div', {'class': 'card'})
            for day in self.list_of_days:
                if len(self.weather) < days_range:
                    if day.text:
                        self.dict_filler(day)

    def dict_filler(self, day):
        """ Вносим данные в словарь"""
        months = ['январ',
                  'феврал',
                  'март',
                  'апрел',
                  'ма',
                  'июн',
                  'июл',
                  'август',
                  'сентябр',
                  'октябр',
                  'ноябр',
                  'декабр',
                  ]

        # day info
        day_number = day.find('strong', {'class': 'forecast-details__day-number'})
        month = day.find('span', {'class': 'forecast-details__day-month'})
        day_name = day.find('span', {'class': 'forecast-details__day-name'})
        date_for_user = f'{day_number.text} {month.text}'
        # Создаю поле с датой. Месяц беру из списка, так как у яндекса месяц представлен только названием, не номером
        for one_month in months:
            if one_month in month.text:
                month_number = months.index(one_month) + 1
                break
        date = datetime.date(datetime.datetime.now().year, month_number, int(day_number.text)).strftime('%d-%m-%Y')
        self.weather[date] = OrderedDict()
        # day weather
        parts_of_day = day.find_all('div', {'class': 'weather-table__daypart'})
        temperatures = day.find_all('div', {'class': 'weather-table__temp'})
        conditions = day.find_all('td',
                                  {'class':
                                   'weather-table__body-cell weather-table__body-cell_type_condition'})
        pressures = day.find_all('td',
                                 {'class':
                                  'weather-table__body-cell weather-table__body-cell_type_air-pressure'})
        humidities = day.find_all('td',
                                  {'class':
                                   'weather-table__body-cell weather-table__body-cell_type_humidity'})
        wind_speeds = day.find_all('span', {'class': 'wind-speed'})
        wind_directions = day.find_all('div', {'class': 'weather-table__wind-direction'})
        feels = day.find_all('td',
                             {'class': 'weather-table__body-cell weather-table__body-cell_type_feels-like'})
        for part, condition, temperature, pressure, humidity, wind_speed, wind_direction, feel in \
                zip(parts_of_day, conditions, temperatures, pressures, humidities, wind_speeds,
                    wind_directions, feels):
            day_part = part.text.capitalize()
            self.weather[date][day_part] = OrderedDict()
            self.weather[date][day_part]['date'] = date
            self.weather[date][day_part]['day_name'] = day_name.text.capitalize()
            self.weather[date][day_part]['date_for_user'] = date_for_user
            self.weather[date][day_part]['day_part'] = day_part
            self.weather[date][day_part]['condition'] = condition.text
            self.weather[date][day_part]['temp'] = temperature.text
            self.weather[date][day_part]['pressure'] = pressure.text
            self.weather[date][day_part]['humidity'] = humidity.text
            self.weather[date][day_part]['wind_speed'] = wind_speed.text
            self.weather[date][day_part]['wind_direction'] = wind_direction.text
            self.weather[date][day_part]['feels_like'] = feel.text


class ImageMaker:
    CONDITION_IMAGES = {
        'Ясно': 'img/sun.jpg',
        'Облачно': 'img/cloud.jpg',
        'Пасмурно': 'img/cloud.jpg',
        'Снег': 'img/snow.jpg',
        'Дождь': 'img/rain.jpg',
    }

    def __init__(self, weather_dict):
        self.card = 'img/template.jpg'
        self.card_cv = cv2.imread(self.card)
        self.im_width = self.card_cv.shape[1]
        self.im_height = self.card_cv.shape[0]
        self.weather = weather_dict
        self.card_cv_final = None

    def view_image(self, name_of_window):
        """Вывод карточки на экран"""
        cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
        cv2.imshow(name_of_window, self.card_cv_final)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def make_card(self, days):
        """Делаем карточку"""
        self.gradient(days)
        args = self.info_to_card(days)
        self.from_pil_to_cv()
        if days == 1:
            self.part_day_image(args)
        else:
            self.days_images(*args)

    def info_to_card(self, days):
        if days == 1:
            # делаем карточку по дате
            today = datetime.date.today().strftime('%d-%m-%Y')
            draw = ImageDraw.Draw(self.card_cv)
            day_part_font = ImageFont.truetype('Microsoft_Sans_Serif.ttf', size=7, )
            font = ImageFont.truetype('Microsoft_Sans_Serif.ttf', size=10)
            day_title_font = ImageFont.truetype('Microsoft_Sans_Serif.ttf', size=15)
            headers = ['', '', 'Давление,\nмм.р.ст', 'Влажность', 'Ветер,\nм/c', 'Ощущается\nкак']
            day_weather = self.weather[today]
            text = f'Сегодня {self.weather[today]["date_for_user"]}'
            draw.text((8, 8), text, font=day_title_font, fill='black')  # День недели и дата
            height = 50
            x = 85
            for header in headers:  # заголовки
                draw.text((x, 20), header, font=day_part_font, fill='black', spacing=1)
                x += 75
            for day_part, day_part_weather in day_weather.items():  # часть дня и температура в это время
                if day_part not in ['day_name', 'date_for_user']:
                    draw.text((10, height - 20), day_part, font=day_part_font, fill='black')
                    draw.text((10, height), day_weather[day_part]['temp'], font=font, fill='black')
                    x = 85
                    for condition, value in day_part_weather.items():  # данные за часть дня
                        if condition not in ['temp', 'wind_direction']:
                            if condition == 'wind_speed':
                                value = f'{value} {day_part_weather["wind_direction"]}'
                            x += 75
                            if len(value) > 10:
                                value = '\n'.join(value.split())
                            draw.text((x, height), value, font=font, fill='black', spacing=1)
                    height += 60
            return day_weather
        else:
            # Делаем карточку на заданное количество дней
            day_title_font = ImageFont.truetype('Microsoft_Sans_Serif.ttf', size=10)
            font = ImageFont.truetype('Microsoft_Sans_Serif.ttf', size=10)
            x = 10
            y = 10
            rows = math.ceil(len(self.weather) / 4)
            x_step = int(self.im_width / 4)
            y_step = int(self.im_height / rows)
            column = 0
            for day, weather in self.weather.items():
                if column == 4:
                    y += y_step
                    x = 10
                    column = 0
                draw = ImageDraw.Draw(self.card_cv)
                draw.text((x, y), weather["day_name"], font=day_title_font, fill='black')
                draw.text((x, y + 20), weather["date_for_user"], font=day_title_font, fill='black')
                temp = f'{weather["Днём"]["temp"]}'
                draw.text((x, y + 50), temp, font=font, fill='black')
                x += x_step
                column += 1
            return x_step, y_step

    def days_images(self, x_step, y_step):
        """ Добавляем картинку к каждому дню"""
        x = 85
        y = 30
        column = 0
        for weather in self.weather.values():
            if column == 4:
                y += y_step
                x = 85
                column = 0
            condition = weather['Днём']['condition']
            self.condition_image(condition, y, y + 30, x, x + 30)
            x += x_step
            column += 1

    def part_day_image(self, day_weather):
        """ Добавляем картинку к каждой части дня"""
        day_parts_offset = {
            'Утром': [40, 70],
            'Днём': [100, 130],
            'Вечером': [160, 190],
            'Ночью': [220, 250]
        }
        for day_part in day_weather:
            if day_part not in ['day_name', 'date_for_user']:
                day_y_start, day_y_end = day_parts_offset[day_part]
                condition = day_weather[day_part]['condition']
                self.condition_image(condition, day_y_start, day_y_end, 95, 125)

    def condition_image(self, *args):
        """Вставляем картинку сосгласно состоянию погоды"""
        condition, y_start, y_end, x_start, x_end = args
        for key in self.CONDITION_IMAGES.keys():
            if key.lower() in condition.lower():
                weather_img = cv2.imread(self.CONDITION_IMAGES[key])
                scale_percent = 30  # Процент от изначального размера
                width = int(weather_img.shape[1] * scale_percent / 100)
                height = int(weather_img.shape[0] * scale_percent / 100)
                dim = (width, height)
                weather_img = cv2.resize(weather_img, dim, interpolation=cv2.INTER_AREA)
                self.card_cv_final[y_start:y_end, x_start:x_end] = weather_img
                break

    def from_cv_to_pil(self):
        # превращаем в PIL, так как opencv не умеет в кириллицу
        self.card_cv = cv2.cvtColor(self.card_cv, cv2.COLOR_BGR2RGB)
        self.card_cv = Image.fromarray(self.card_cv)

    def from_pil_to_cv(self):
        self.card_cv_final = numpy.asarray(self.card_cv)
        self.card_cv_final = self.card_cv_final.copy()

    def gradient(self, days):
        # делаем фон в сv
        self.card_cv = cv2.cvtColor(self.card_cv, cv2.COLOR_BGR2RGB)
        if days == 1:
            today = datetime.date.today().strftime('%d-%m-%Y')
            condition = self.weather[today]['Днём']['condition']
            for i in range(self.im_height):
                conditions_gradients = {
                    'Cнег': (53 + i, 240 + i, 255),
                    'Дождь': (53 + i, 100 + i, 255),
                    'Ясно': (255, 255, 255 - i),
                    'Облачно': (50 + i, 50 + i, 50 + i)
                }
                for color in conditions_gradients:
                    if color.lower() in condition.lower():
                        cv2.line(self.card_cv, (0, i), (self.im_width, i), conditions_gradients[color], thickness=1)
                        break
        else:
            for i in range(self.im_height):
                cv2.line(self.card_cv, (0, i), (self.im_width, i), (53 + i, 240 + i, 255), thickness=1)
        self.from_cv_to_pil()


class DataBaseUpdater:

    def __init__(self):
        self.database = None

    def db_init(self):
        database_proxy = peewee.DatabaseProxy()
        self.database = peewee.SqliteDatabase('weather')
        database_proxy.initialize(self.database)

    def data_getter(self, days, date_from=None):
        """  Метод получает данные из базы"""
        return_dict = OrderedDict()
        today = datetime.date.today()
        if date_from is None:
            date_from = datetime.date.today()
        # Берем данные из базы
        date_to = (today + datetime.timedelta(days=days - 1)).strftime('%d-%m-%Y')
        res = DayWeather.select().\
            where(DayWeather.date.between(date_from.strftime('%d-%m-%Y'), date_to))
        for day_part in res:
            date_for_user = DayWeather.get(DayWeather.date == day_part.date).date_for_user
            date = day_part.date
            if date == today.strftime('%d-%m-%Y'):
                day_name = 'Сегодня'
            elif date == (today + datetime.timedelta(days=1)).strftime('%d-%m-%Y'):
                day_name = 'Завтра'
            else:
                days = ['Понедельник',
                        'Вторник',
                        'Среда',
                        'Четверг',
                        'Пятница',
                        'Суббота',
                        'Воскресенье',
                        ]
                day_number = datetime.datetime.strptime(date, '%d-%m-%Y').weekday()
                day_name = days[day_number]
            if date not in return_dict:
                return_dict[date] = OrderedDict()
            return_dict[date]['day_name'] = day_name
            return_dict[date]['date_for_user'] = date_for_user
            #  Заполняем словарь с результатом
            day_part_name = day_part.day_part
            return_dict[day_part.date][day_part_name] = {}
            return_dict[day_part.date][day_part_name]['condition'] = day_part.condition
            return_dict[day_part.date][day_part_name]['temp'] = day_part.temp
            return_dict[day_part.date][day_part_name]['pressure'] = day_part.pressure
            return_dict[day_part.date][day_part_name]['humidity'] = day_part.humidity
            return_dict[day_part.date][day_part_name]['wind_speed'] = day_part.wind_speed
            return_dict[day_part.date][day_part_name]['wind_direction'] = day_part.wind_direction
            return_dict[day_part.date][day_part_name]['feels_like'] = day_part.feels_like
        return return_dict

    def data_poster(self, days):
        """  Метод добавляет данные в базу"""
        weather_request = WeatherMaker()
        weather_request.make_weather_for_day_range(days)
        weather_to_database = weather_request.weather
        for date, day_info in weather_to_database.items():
            self.database.create_tables([DayWeather])
            query = DayWeather.select().where(DayWeather.date == date)
            if len(query):
                for day_part_info in day_info.values():
                    new_record = {**day_part_info}
                    DayWeather.update(**new_record)
            else:
                for day_part_info in day_info.values():
                    new_record = {**day_part_info}
                    DayWeather.create(**new_record)


class WeatherManager:

    def __init__(self, *args):
        self.days_put, self.days_get, self.first_arg, self.second_arg = args
        self.weather = None

    def manage(self):
        base = DataBaseUpdater()
        base.db_init()
        self.get_data_for_last_week(base)

        if self.days_put:
            base.data_poster(self.days_put)
        if self.days_get:
            self.weather = base.data_getter(self.days_get)
            if self.days_get > 10:
                print('Давайте не будем загядывать так далеко вперед.\n'
                      'Погода может поменяться.\n'
                      'Посмотрите прогноз на ближайшие даты.\n')
            elif len(self.weather) < self.days_get:
                print(f'Дней, внесенных в базу на {self.days_get - len(self.weather)} меньше чем Вы запросили.\n'
                      f'Если хотите увидеть больше данных внесите их сначала в базу.\n'
                      f'Используйте: --put={self.days_get}\n'
                      f'Посмотрите прогноз на ближайшие даты.\n')
            if any(arg == 'print' for arg in [self.first_arg, self.second_arg]):
                print('Запрошенный Вами прогноз')
                if self.days_get == 1:
                    self.print_today(self.weather)
                else:
                    self.print_days(self.weather)
            if any(arg == 'makecard' for arg in [self.first_arg, self.second_arg]):
                weather_card = ImageMaker(self.weather)
                weather_card.make_card(self.days_get)
                weather_card.view_image('weather')

    def get_data_for_last_week(self, base):
        """Метод выводит данные за прошедшую неделю, либо данные, которые есть в базе, если на неделю их не набралось"""
        print('\nДанные за прошедшую неделю')
        date_from = datetime.date.today() - datetime.timedelta(days=7)
        data = base.data_getter(days=7, date_from=date_from)
        self.print_days(data)

    def print_today(self, weather):
        """Вывод на экран данных за один день"""
        for day in weather.values():
            print(f'{day["day_name"]} {day["date_for_user"]}')
            print(f'+{"":-^11}+{"":-^11}+{"":-^25}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^15}+')
            print(f'+{"":^11}+{"Температура":^11}+{"На улице":^25}+'
                  f'{"Давление":^11}+{"Влажность":^11}+{"Ветер, м/с":^11}+{"Направление":^11}+{"Ощущается как":^15}+')
            for day_part, day_data in day.items():
                if day_part not in ['day_name', 'date_for_user']:
                    print(f'+{"":-^11}+{"":-^11}+{"":-^25}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^15}+')
                    print(f'+{day_part:^11}+'
                          f'{self.info(day, day_part)}')
            print(f'+{"":-^11}+{"":-^11}+{"":-^25}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^15}+')
            print()

    def print_days(self, weather):
        """Вывод на экран данных на запрошенное количество дней"""
        print(f'+{"":-^15}+{"":-^15}+{"":-^11}+{"":-^25}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^15}+')
        print(f'+{"День недели":^15}+{"Дата":^15}+{"Температура":^11}+{"На улице":^25}+'
              f'{"Давление":^11}+{"Влажность":^11}+{"Ветер, м/с":^11}+{"Направление":^11}+{"Ощущается как":^15}+')
        for day, day_weather in weather.items():
            print(f'+{"":-^15}+{"":-^15}+{"":-^11}+{"":-^25}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^15}+')
            print(f'+{day_weather["day_name"]:^15}+'
                  f'{day_weather["date_for_user"]:^15}+'
                  f'{self.info(day_weather, "Днём")}')
        print(f'+{"":-^15}+{"":-^15}+{"":-^11}+{"":-^25}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^11}+{"":-^15}+')
        print()

    def info(self, weather, day_part):
        return f'{weather[day_part]["temp"]:^11}+' \
               f'{weather[day_part]["condition"]:^25}+'\
               f'{weather[day_part]["pressure"]:^11}+'\
               f'{weather[day_part]["humidity"]:^11}+'\
               f'{weather[day_part]["wind_speed"]:^11}+'\
               f'{weather[day_part]["wind_direction"]:^11}+'\
               f'{weather[day_part]["feels_like"]:^15}+'
