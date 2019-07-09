import requests
import pandas as pd
from pandas.compat import StringIO
import csv
import sqlite3
import json

class Scenario:
    def __init__(self, buy_high, buy_average, buy_low, sell_high, sell_average, sell_low, dividend, buy_date, sell_date, timeframe_buy, timeframe_sell):
        self.timeframe_buy = timeframe_buy
        self.timeframe_sell = timeframe_sell
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
        self.dividend = dividend
        self.buy_date = buy_date
        self.sell_date = sell_date

class Company:
    def __init__(self, name, ticker, market, currency, historic_data, dividend_data):
        self.name = name 
        self.ticker = ticker
        self.currency = currency
        self.market = market 
        self.historic_data = historic_data
        self.dividend_data = dividend_data
        self.scenarios = {}

    def fill_tables(self, year, hv):
        hv_date = self.dividend_data[hv]["date"]
        print(hv_date)
        db_connection = sqlite3.connect('databases/div_trade_v8.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT ID FROM Companies WHERE Company = '{self.name}'")
        company_id = db_cursor.fetchone()
        company_id = company_id[0]
        for i in self.scenarios[hv_date]:
            '''print(f"""INSERT INTO '{year}' ('Company_ID', 'Timeframe_Buy','Timeframe_Sell','High_%','Avg_%','Low_%', 'Dividend_%','Dividends','Day_Line200', 'Buy_Date', 'Sell_Date',
                            'Buy_High', 'Buy_Low', 'Sell_High', 'Sell_Low') 
                            VALUES ('{company_id}', '{i.timeframe_buy}','{i.timeframe_sell}',{i.best_percent},{i.medium_percent},{i.worst_percent}, {self.dividend_data[hv]["percentage"]} , {i.dividend}, 0,
                            '{i.buy_date}', '{i.sell_date}',
                            {i.buy_high},{i.buy_low},{i.sell_high},{i.sell_low})""")'''
            db_cursor.execute(f"""INSERT INTO '{year}' ('Company_ID', 'Timeframe_Buy','Timeframe_Sell','High_%','Avg_%','Low_%', 'Dividend_%','Dividends','Day_Line200', 'Buy_Date', 'Sell_Date',
                            'Buy_High', 'Buy_Low', 'Sell_High', 'Sell_Low') 
                            VALUES ('{company_id}', '{i.timeframe_buy}','{i.timeframe_sell}',{i.best_percent},{i.medium_percent},{i.worst_percent}, {self.dividend_data[hv]["percentage"]} , {i.dividend}, 0,
                            '{i.buy_date}', '{i.sell_date}',
                            {i.buy_high},{i.buy_low},{i.sell_high},{i.sell_low})""")
        db_connection.commit()
        db_cursor.close()
        print(f"{year} tables filled")

    def write_hv_to_db(self, hv):
        db_connection = sqlite3.connect('databases/div_trade_v8.db')
        db_cursor = db_connection.cursor()
        year = str(self.dividend_data[hv]["date"])[0:4]
        db_cursor.execute(f"SELECT Company FROM Companies WHERE Company = '{self.name}'")
        company = db_cursor.fetchone()
        if not company:
            db_cursor.execute(f"INSERT INTO Companies (Company, Market, Years, Currency, Ticker) VALUES ('{self.name}', '{self.market}', 0, '{self.currency}', '{self.ticker}')")
            print("company added")   
        try:
            db_cursor.execute(f"""CREATE TABLE "{year}" 
                        ("ID" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "Company_ID"	INTEGER NOT NULL,
                        "Timeframe_Buy"	INTEGER NOT NULL,
                        "Timeframe_Sell" INTEGER NOT NULL,
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
        self.fill_tables(year, hv)

    def add_scenario(self, scenario, date):
        if date not in self.scenarios.keys():
            self.scenarios[date] = [scenario]
        else:
            self.scenarios[date].append(scenario)

    def get_sell_prices(self, index, timeframe):
        if timeframe == 0:
            date = self.historic_data[index]["date"]
            high = round(float(self.currency_conversion(self.historic_data[index]["high"], date)),2)
            low = round(float(self.currency_conversion(self.historic_data[index]["low"], date)),2)
            average = round((high+low)/2,2)       
        else:
            sell_index = index + timeframe
            if sell_index >= len(self.historic_data):
                sell_index = len(self.historic_data)-1
            sell_day = self.historic_data[sell_index]
            date = sell_day["date"] 
            high = round(float(self.currency_conversion(sell_day["high"],date)),2)
            low = round(float(self.currency_conversion(sell_day["low"],date)),2)
            average = round((high+low)/2,2)  
        return high, average, low, date

    def get_buy_prices(self, index, timeframe):
        buy_index = index - timeframe
        if buy_index < 0:
            buy_index = 0
        buy_day = self.historic_data[buy_index]   
        date = buy_day["date"] 
        high = round(float(self.currency_conversion(buy_day["high"],date)),2)
        low = round(float(self.currency_conversion(buy_day["low"],date)),2)
        average = round((high+low)/2,2)  
        return high, average, low, date

    def calculate_dividend_percentage(self, dividend_value, dividend_date, ex_day):
        ex_day_close = round(float(self.currency_conversion(ex_day["close"], ex_day["date"])),2)
        dividend_percentage = round(dividend_value/ex_day_close*100,2)
        for index in self.dividend_data:
            if self.dividend_data[index]["date"] == dividend_date:
                self.dividend_data[index]["percentage"] = dividend_percentage

    def currency_conversion(self, to_convert, date):
        if self.currency != "EUR" and self.currency != "ILS":
            with open(f"currencies/foreign-eur/{self.currency}EUR.FOREX.csv", "r") as currency_data:
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

        if self.currency == "ILS":
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
        if self.currency == "EUR":
            return to_convert

    def get_day_by_date(self, date):
        for index in range(len(self.historic_data)):
            if self.historic_data[index]["date"] == date:
                return self.historic_data[index], index

    def calc_scenario(self, hv, timeframe_buy, timeframe_sell):
        ex_day, index = self.get_day_by_date(self.dividend_data[hv]["date"])
        dividend_value = float(self.currency_conversion(self.dividend_data[hv]["value"],self.dividend_data[hv]["date"]))
        self.calculate_dividend_percentage(dividend_value, self.dividend_data[hv]["date"], ex_day)
        buy_high, buy_average, buy_low, buy_date = self.get_buy_prices(index, timeframe_buy)
        sell_high, sell_average, sell_low, sell_date= self.get_sell_prices(index, timeframe_sell)
        scenario = Scenario(buy_high, buy_average, buy_low, sell_high, sell_average, sell_low, dividend_value, buy_date, sell_date, timeframe_buy, timeframe_sell)
        self.add_scenario(scenario, self.dividend_data[hv]["date"])
        


def get_stock_info(ticker, api_token, params):
    session=requests.Session()
    url_stock_info = f"https://eodhistoricaldata.com/api/search/{ticker}?api_token={api_token}"
    response_stock_info = session.get(url_stock_info, params=params)
    if response_stock_info.status_code == requests.codes.ok:
        stock_info = json.loads(response_stock_info.text)
        stock_info = stock_info[0]
        name = stock_info["Name"]
        if "'" in name:
            name = name.replace("'", "")
        currency = stock_info["Currency"]
        if currency == "GBX":
            currency = "GBP"
        market = stock_info["Country"]
        exchange = stock_info["Exchange"]
        eod_ticker = f"{ticker}.{exchange}"
        return name, currency, market, eod_ticker

def get_historic_data(ticker, api_token, params):
    session=requests.Session()
    url_historic= f"https://eodhistoricaldata.com/api/eod/{ticker}?api_token={api_token}&fmt=json"
    reponse_historic = session.get(url_historic, params=params)
    if reponse_historic.status_code == requests.codes.ok:
        historic_data = json.loads(reponse_historic.text)
        return historic_data

def get_dividend_data(ticker, api_token, params):
    session=requests.Session()
    url_dividends= f"https://eodhistoricaldata.com/api/div/{ticker}?api_token={api_token}&from=2000-01-01&fmt=json"
    reponse_dividends = session.get(url_dividends, params=params)
    if reponse_dividends.status_code == requests.codes.ok:
        dividend_data = json.loads(reponse_dividends.text)
        return dividend_data

def get_eod_data(ticker, api_token):
    if "." in ticker:
        search_ticker = ticker[:ticker.find(".")]
    else:
        search_ticker = ticker
    print(search_ticker)
    params = {"api_token":api_token}
    name, currency, market, eod_ticker = get_stock_info(search_ticker, api_token, params)
    historic_data = get_historic_data(eod_ticker, api_token, params)
    dividend_data = get_dividend_data(eod_ticker, api_token, params)
    company = Company(name, ticker, market, currency, historic_data, dividend_data )
    print(name, currency)
    return company

def create_timeframes():
    timeframes = {}
    timeframe_buy = 0 # Default 0
    while timeframe_buy < 60: #Default 60
        timeframe_buy += 1
        for i in range(11): # Default 11
            timeframe_sell = i
            timeframe = f"{timeframe_buy}-{timeframe_sell}"
            timeframes[timeframe] = [timeframe_buy,timeframe_sell]
    return timeframes

def check_zar(ticker, api_token):
    params = {"api_token":api_token}
    session=requests.Session()
    url_stock_info = f"https://eodhistoricaldata.com/api/search/{ticker}?api_token={api_token}"
    response_stock_info = session.get(url_stock_info, params=params)
    if response_stock_info.status_code == requests.codes.ok:
        stock_info = json.loads(response_stock_info.text)
        if stock_info:
            currency = stock_info[0]["Currency"]
            if currency == "ZAR":
                return True

def get_ticker():
    db_connection = sqlite3.connect('databases/div_trade_v7.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Ticker FROM Companies")
    total_ticker= db_cursor.fetchall()
    total_tickers = []
    for ticker in total_ticker:
        total_tickers.append(ticker[0])
    db_connection.close()
    return total_tickers

if __name__ == "__main__":
    api_token="5d19ac0dbbdd85.51123060"
    total_ticker = get_ticker()
    total_ticker = total_ticker[total_ticker.index("SDR.L"):]
    timeframes = create_timeframes()
    for ticker in total_ticker:
        if not check_zar(ticker, api_token):
            company = get_eod_data(ticker, api_token)
            for hv in company.dividend_data:
                for timeframe in timeframes:
                    company.calc_scenario(hv, timeframes[timeframe][0], timeframes[timeframe][1])
                company.write_hv_to_db(hv)