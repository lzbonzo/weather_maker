# -*- coding: utf-8 -*-

import argparse
import weather_maker


if __name__ == '__main__':
    weather_pars = argparse.ArgumentParser(description='Get Weather')
    weather_pars.add_argument('--put', type=int, action='store')
    weather_pars.add_argument('--get', type=int, action='store')
    weather_pars.add_argument('first_arg', nargs='?')
    weather_pars.add_argument('second_arg', nargs='?')
    weather_args = weather_pars.parse_args()
    days_put = weather_args.put
    days_get = weather_args.get
    first_arg = weather_args.first_arg
    second_arg = weather_args.second_arg
    manager = weather_maker.WeatherManager(days_put, days_get, first_arg, second_arg)
    manager.manage()
