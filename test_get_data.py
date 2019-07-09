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
    db_connection = sqlite3.connect('databases/div_trade_v8b.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT ID FROM Companies WHERE Company = '{name}'")
    company_id = db_cursor.fetchone()
    company_id = company_id[0]
    for i in scenarios:
        # print(f"""INSERT INTO '{year}' ('Company_ID', 'Timeframe','High_%','Avg_%','Low_%', 'Dividends','Day_Line200', 'Buy_Date', 'Sell_Date',
        #                'Buy_High', 'Buy_Low', 'Sell_High', 'Sell_Low')
        #                VALUES ('{company_id}', '{i}',{scenarios[i].best_percent},{scenarios[i].medium_percent},{scenarios[i].worst_percent},{dividend_percentage},
        #                {scenarios[i].day_line200}, '{scenarios[i].buy_date}', '{scenarios[i].sell_date}',
        #                {scenarios[i].buy_high},{scenarios[i].buy_low},{scenarios[i].sell_high},{scenarios[i].sell_low})""")
        db_cursor.execute(f"""INSERT INTO '{year}' ('Company_ID', 'Timeframe','High_%','Avg_%','Low_%', 'Dividend_%','Dividends','Day_Line200', 'Buy_Date', 'Sell_Date',
                        'Buy_High', 'Buy_Low', 'Sell_High', 'Sell_Low') 
                        VALUES ('{company_id}', '{i}',{scenarios[i].best_percent},{scenarios[i].medium_percent},{scenarios[i].worst_percent},{dividend_percentage}, {scenarios[i].dividend},
                        {scenarios[i].day_line200}, '{scenarios[i].buy_date}', '{scenarios[i].sell_date}',
                        {scenarios[i].buy_high},{scenarios[i].buy_low},{scenarios[i].sell_high},{scenarios[i].sell_low})""")
    db_connection.commit()
    db_cursor.close()
    print(f"{year} tables filled")


def write_year_to_db(scenarios, date, name, dividend_percentage, market, currency, ticker):
    db_connection = sqlite3.connect('databases/div_trade_v8b.db')
    db_cursor = db_connection.cursor()
    year = str(date)[0:4]
    db_cursor.execute(
        f"SELECT Company FROM Companies WHERE Company = '{name}'")
    company = db_cursor.fetchone()
    if not company:
        db_cursor.execute(
            f"INSERT INTO Companies (Company, Market, Years, Currency, Ticker) VALUES ('{name}', '{market}', 0, '{currency}', '{ticker}')")
        print("company added")
    try:
        db_cursor.execute(f"""CREATE TABLE "{year}" 
                    ("ID" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                     "Company_ID"	INTEGER NOT NULL,
                     "Timeframe"	INTEGER NOT NULL,
                     "High_%"	INTEGER NOT NULL, 
                     "Avg_%"	INTEGER NOT NULL,
                     "Low_%"	INTEGER NOT NULL, 
                     "Dividend_%" INTEGER NOT NULL, 
                     "Dividends" INTEGER NOT NULL, 
                     "Day_Line200" INTEGER,
                     "Buy_Date" TEXT,
                     "Sell_Date" TEXT,
					 "Buy_High" INTEGER,
					 "Buy_Low" INTEGER,
					 "Sell_High" INTEGER,
					 "Sell_Low" INTEGER)""")
        #print(f"{year} tables created")
    except sqlite3.OperationalError:
        pass
    db_connection.commit()
    db_cursor.close()
    #print("fill_tables done")
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
        self.average = (self.high + self.low)/2
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
        while timeframe_buy < 60:  # Default 60
            timeframe_buy += 1
            day_line200 = calc_day_line200(timeframe_buy, calc, date, dates)
            for i in range(11):  # Default 11
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


def start(company):
    currency = data_yahoo.info["currency"]
    currency = currency.upper()
    market = data_yahoo.info["market"]
    highs = data["high"]
    lows = data["low"]
    closes = data["close"]
    dates = data["date"]
    index = check_2001(dates)
    if index == None:
        index = 0
    highs = rebuild_lists(highs, index)
    lows = rebuild_lists(lows, index)
    closes = rebuild_lists(closes, index)
    dates = rebuild_lists(dates, index)
    dividend_amounts = data_yahoo.dividends
    dividend_days = data_yahoo.dividends.keys()
    div_index = check_same_beginning(dividend_days, dates)
    dividend_amounts = dividend_amounts[div_index:]
    dividend_days = dividend_days[div_index:]

    temp_list = []
    for i in dividend_days:
        temp_list.append(str(i)[0:10])
    dividend_days = temp_list

    days = []
    temp_dividends = {}
    highs = check_for_null(highs, "first")
    lows = check_for_null(lows, "first")
    closes = check_for_null(closes, "first")
    if currency != "EUR" and currency != "ILS":
        print(currency)
        with open(f"currencies/foreign-eur/{currency}EUR.FOREX.csv", "r") as currency_data:
            table = csv.reader(currency_data)
            cur_dates = []
            cur_close = []
            for row in table:
                cur_dates.append(row[0])
                cur_close.append(row[4])
            # print(type(high))
        for i in range(len(highs)):
            conversion_amount = find_cur_date(dates[i], cur_dates, cur_close)
            high = highs[i]
            low = lows[i]
            close = closes[i]
            high = round(float(high)*float(conversion_amount), 2)
            low = round(float(low)*float(conversion_amount), 2)
            close = round(float(close)*float(conversion_amount), 2)
            days.append(Day(dates[i], high, low, close))
        for n in range(len(dividend_days)):
            conversion_amount = find_cur_date(
                dividend_days[n], cur_dates, cur_close)
            dividend_amount = round(
                float(dividend_amounts[n])*float(conversion_amount), 2)
            temp_dividends[dividend_days[n]] = dividend_amount
    if currency == "ILS":
        print(currency)
        with open(f"currencies/foreign-eur/fx_daily_ILS_EUR.csv", "r") as currency_data:
            table = csv.reader(currency_data)
            cur_dates = []
            cur_close = []
            for row in table:
                cur_dates.append(row[0])
                cur_close.append(row[4])
            # print(type(high))
        for i in range(len(highs)):
            conversion_amount = find_cur_date(dates[i], cur_dates, cur_close)
            high = highs[i]
            low = lows[i]
            close = closes[i]
            high = round(float(high)*float(conversion_amount), 2)
            low = round(float(low)*float(conversion_amount), 2)
            close = round(float(close)*float(conversion_amount), 2)
            days.append(Day(dates[i], high, low, close))
        for n in range(len(dividend_days)):
            conversion_amount = find_cur_date(
                dividend_days[n], cur_dates, cur_close)
            dividend_amount = round(
                float(dividend_amounts[n])*float(conversion_amount), 2)
            temp_dividends[dividend_days[n]] = dividend_amount
    if currency == "EUR":
        for i in range(len(highs)):
            days.append(Day(dates[i], highs[i], lows[i], closes[i]))
        for n in range(len(dividend_days)):
            temp_dividends[dividend_days[n]] = dividend_amounts[n]
    dividends[company] = temp_dividends
    # create Days with date, high, low
    print("step1 done")
    calc = DividendCalculator(days)

    # start calculations
    #
    get_prices(calc, company, name, dividends, market, currency)


if __name__ == "__main__":
    AV = AlphaVantage(
        api_key="5UV3KMIGR8VPA5AW",
        premium=True,
        output_size='full',
        datatype='json',
        clean=True,)
    db_connection = sqlite3.connect('databases/div_trade_v7.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Ticker FROM Companies")
    db_ticker = db_cursor.fetchall()
    db_connection.close()
    total_ticker = []
    for ticker in db_ticker:
        if ticker[0] not in total_ticker:
            total_ticker.append(ticker[0])
    total_ticker = total_ticker[total_ticker.index("T")+2:]
    for company in total_ticker:
        start(company)
