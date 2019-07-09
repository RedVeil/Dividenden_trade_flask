import datetime
import matplotlib.pyplot as plt
import sqlite3
import requests
from alphaVantageAPI.alphavantage import AlphaVantage
import fix_yahoo_finance as yf
import numpy
import time
import csv
import json


def fill_tables(scenarios, year, dividend_percentage, name):
    for i in scenarios:
        print(f"""{year} 
        (Timeframe: {i},High_%: {scenarios[i].best_percent},Avg_%: {scenarios[i].medium_percent},Low_%: {scenarios[i].worst_percent}, 
        Dividends_%: {dividend_percentage},Day_Line200: {scenarios[i].day_line200}, 
        Buy_Date: {scenarios[i].buy_date}, Sell_Date: {scenarios[i].sell_date},
        Buy_High: {scenarios[i].buy_high}, Buy_Low: {scenarios[i].buy_low}, Sell_High: {scenarios[i].sell_high}, Sell_Low: {scenarios[i].sell_low})""")


def write_year_to_db(scenarios, date, name, dividend_percentage, market, currency, ticker):
    year = str(date)[0:4]
    fill_tables(scenarios, year, dividend_percentage, name)
    return year


class Scenario:
    def __init__(self, buy_high, buy_average, buy_low, sell_high, sell_average, sell_low, dividend, day_line200, buy_date, sell_date):
        self.buy_high = buy_high
        self.buy_low = buy_low
        self.sell_high = sell_high
        self.sell_low = sell_low
        best = round(sell_high + dividend - buy_low, 2)
        medium = round(sell_average + dividend - buy_average, 2)
        worst = round(sell_low + dividend - buy_high, 2)
        self.best_percent = round(best/buy_low*100, 2)
        self.medium_percent = round(medium/buy_average*100, 2)
        self.worst_percent = round(worst/buy_high*100, 2)
        self.day_line200 = round(day_line200, 2)
        self.dividend = dividend
        self.buy_date = buy_date
        self.sell_date = sell_date


class Day:
    def __init__(self, date, high, low, close):
        self.date = date
        self.high = float(high)
        self.low = float(low)
        self.average = round((self.high + self.low)/2,2)
        self.close = (float(close))


class DividendCalculator:
    def __init__(self, in_days):
        self.days = in_days

    def _get_day_by_date(self, date, dates, tries):
        if tries == "first":
            for index in range(0, len(self.days)):
                if self.days[index].date == date:
                    return self.days[index], index
        if tries == "second":
            for i in range(len(dates)):
                if dates[i] == date:
                    date = dates[i+1]
                    for index in range(0, len(self.days)):
                        if self.days[index].date == date:
                            return self.days[index], index

    def _get_buy_prices(self, index, timeframe):
        buy_index = index - timeframe
        if buy_index < 0:
            buy_index = 0
        buy_day = self.days[buy_index]
        high = buy_day.high
        average = buy_day.average
        low = buy_day.low
        date = buy_day.date
        return (high, average, low, date)

    def _get_sell_prices(self, index, timeframe):
        if timeframe == 0:
            high = self.days[index].high
            average = self.days[index].average
            low = self.days[index].low
            date = self.days[index].date
        else:
            sell_index = index + timeframe
            if sell_index >= len(self.days):
                sell_index = len(self.days)-1
            sell_day = self.days[sell_index]
            high = sell_day.high
            average = sell_day.average
            low = sell_day.low
            date = sell_day.date
        return (high, average, low, date)

    def dividend_percentage(self, dividend, ex_day):
        dividend_percentage = round(dividend/ex_day.average*100, 2)
        return dividend_percentage

    def calc_scenario(self, date, timeframe_buy, timeframe_sell, company, dividends, day_line200, dates):
        try:
            ex_day, index = self._get_day_by_date(date, dates, "first")
        except TypeError:
            ex_day, index = self._get_day_by_date(date, dates, "second")
        dividend = dividends[company][date]
        dividend_percentage = self.dividend_percentage(dividend, ex_day)
        buy_high, buy_average, buy_low, buy_date = self._get_buy_prices(
            index, timeframe_buy)
        sell_high, sell_average, sell_low, sell_date = self._get_sell_prices(
            index, timeframe_sell)
        scenario = Scenario(buy_high, buy_average, buy_low, sell_high,
                            sell_average, sell_low, dividend, day_line200, buy_date, sell_date)
        return scenario, dividend_percentage


def calc_day_line200(timeframe, calc, date, dates):
    # print(calc.days[0].date)
    try:
        ex_day, index = calc._get_day_by_date(date, dates, "first")
    except TypeError:
        ex_day, index = calc._get_day_by_date(date, dates, "second")
    # print(index)
    start = index - timeframe - 200

    end = index - timeframe

    if start < 0:
        start = 0
    if end > len(calc.days):
        end = len(calc.days)-1
    # print(start)
    # print(end)
    days = calc.days[start:end]
    sum_days = 0
    for i in days:
        sum_days += i.close
    if len(days) < 200 and len(days) > 0:
        day_line200 = sum_days/len(days)
    day_line200 = sum_days/200
    buy_price = calc.days[start].close
    if day_line200 == 0.0:
        day_line200 = buy_price
    if buy_price == 0.0:
        buy_price = calc.days[start+1].close
    try:
        day_line200 = buy_price/day_line200
    except ZeroDivisionError:
        print(buy_price, day_line200)
    return day_line200


def update_year_count(name):
    db_connection = sqlite3.connect('databases/div_trade_v8b.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Years FROM Companies WHERE Company = '{name}'")
    years_count = db_cursor.fetchone()
    new_year_count = years_count[0]+1
    db_cursor.execute(
        f"UPDATE Companies SET Years = {new_year_count} WHERE Company = '{name}'")
    db_connection.commit()
    db_cursor.close()


def get_prices(calc, company, name, dividends, market, currency):
    dates = list(dividends[company].keys())
    for date in dates:
        scenarios = {}
        timeframe_buy = 0  # Default 0
        while timeframe_buy < 1:  # Default 60
            timeframe_buy += 1
            day_line200 = calc_day_line200(timeframe_buy, calc, date, dates)
            for i in range(1):  # Default 11
                timeframe_sell = i
                scenario, dividend_percentage = calc.calc_scenario(
                    date, timeframe_buy, timeframe_sell, company, dividends, day_line200, dates)
                period = f"{timeframe_buy}-{timeframe_sell}"
                scenarios[period] = scenario
        write_year_to_db(scenarios, date, name,
                         dividend_percentage, market, currency, company)


def check_for_null(liste, tries):
    if tries == "first":
        try:
            for i in range(len(liste)):
                if str(liste[i]) == "nan" or liste[i] == 0.0:
                    new_index = i-1
                    if new_index < 0:
                        new_index = i+1
                    liste[i] = liste[new_index]
            return liste
        except TypeError:
            check_for_null(liste, "second")
    if tries == "second":
        for i in range(len(liste)):
            if str(liste[i]) == "nan" or liste[i] == 0.0:
                new_index = i-2
                if new_index < 0:
                    new_index = i+2
                liste[i] = liste[new_index]
            else:
                return liste
    return liste


def check_same_beginning(dividend_days, dates):
    for index in range(len(dates)):
        for i in range(len(dividend_days)):
            if str(dates[index]) == str(dividend_days[i])[:10]:
                return i


def rebuild_lists(liste, index):
    temp_liste = []
    for i in range(index, len(liste)):
        temp_liste.append(liste[i])
    return temp_liste


def check_2001(liste):
    for index in range(0, len(liste)):
        if str(liste[index])[0:4] == "2001":
            return index


def find_cur_date(date, cur_dates, cur_close):
    for i in range(len(cur_dates)):
        if cur_dates[i] == date:
            return cur_close[i]
    return cur_close[-1]



def currency_conversion(to_convert, date, currency):
        if currency != "EUR" and currency != "ILS":
            with open(f"currencies/foreign-eur/{currency}EUR.FOREX.csv", "r") as currency_data:
                table=csv.reader(currency_data)
                conversions = {}
                for row in table:    
                    date = row[0]
                    close = row[4]
                    conversions[date] = close
                for conversion_date in conversions:
                    if conversion_date == date:
                        converted_amount = round(float(conversions[conversion_date])*float(to_convert),2)
                        return converted_amount

        if currency == "ILS":
            with open(f"currencies/foreign-eur/fx_daily_ILS_EUR.csv", "r") as currency_data:
                table=csv.reader(currency_data)
                conversions = {}
                for row in table:    
                    date = row[0]
                    close = row[4]
                    conversions[date] = close
                for conversion_date in conversions:
                    if conversion_date == date:
                        converted_amount = round(float(conversions[conversion_date])*float(to_convert),2)
                        return converted_amount
        if currency == "EUR":
            return to_convert

def start(company):
    currency = "BRL"
    name = "Test Name"
    market = "de_market"
    highs = [9,10,11,12,13]
    lows = [8,9,10,11,12]
    closes = [8,8,8,8,8]
    dates = ["2019-06-23","2019-06-24","2019-06-25","2019-06-26","2019-06-27"]
    dividend_days = ["2019-06-25", "2019-06-26" ]
    dividend_amounts = [1, 1]
    days = []
    dividends = {}
    temp_dividends = {}
    for i in range(len(dates)):
        high = currency_conversion(highs[i], dates[i], currency)
        low = currency_conversion(lows[i], dates[i], currency)
        close = currency_conversion(closes[i], dates[i], currency)
        days.append(Day(dates[i], high, low, close))

    for n in range(len(dividend_days)):
        dividend_amount= currency_conversion(dividend_amounts[n], dividend_days[n], currency)
        temp_dividends[dividend_days[n]] = dividend_amount
    dividends[company] = temp_dividends
    
    for day in days:
        print(f"date: {day.date}, high: {day.high}, low: {day.low}, average: {day.average}, close: {day.close}")
    for key in dividends.keys():
        print(key, dividends[key])

    calc = DividendCalculator(days)
    get_prices(calc, company, name, dividends, market, currency)

start("Test")
