import requests
import csv
import sqlite3
import json
import time


class Day:
    def __init__(self, date, high, low, close, volume):
        self.date = date
        self.high = float(high)
        self.low = float(low)
        self.average = round((self.high + self.low)/2, 2)
        self.close = (float(close))
        self.volume = volume

class Company:
    def __init__(self, name, ticker, exchange, currency):
        self.name = name
        self.ticker = ticker
        self.currency = currency
        self.exchange = exchange
        self.days = []
        self.dividends = {}

    def get_sell_prices(self, index, timeframe):
        if timeframe == 0:
            date = self.days[index].date
            high = round(float(self.currency_conversion(
                self.days[index].high, date)), 2)
            low = round(float(self.currency_conversion(
                self.days[index].low, date)), 2)
            average = round((high+low)/2, 2)
        else:
            sell_index = index + timeframe
            if sell_index >= len(self.days):
                sell_index = len(self.days)-1
            sell_day = self.days[sell_index]
            date = sell_day.date
            high = round(
                float(self.currency_conversion(sell_day.high, date)), 2)
            low = round(
                float(self.currency_conversion(sell_day.low, date)), 2)
            average = round((high+low)/2, 2)
        return high, average, low, date

    def get_buy_prices(self, index, timeframe):
        buy_index = index - timeframe
        if buy_index < 0:
            buy_index = 0
        buy_day = self.days[buy_index]
        date = buy_day.date
        high = buy_day.high
        low = buy_day.low
        average = buy_day.average
        return high, average, low, date

    def calculate_dividend_percentage(self, year, n):
        ex_day = self.get_day_by_date(self.dividends[year][n]["date"])
        if ex_day != "pop":
            dividend_percentage = round(float(self.dividends[year][n]["value"])/ex_day.close*100, 2)
            self.dividends[year][n]["percent"] = dividend_percentage
        

    def convert_other_currency(self, historic_data, dividend_data):
        with open(f"currencies/foreign-eur/{self.currency}EUR.FOREX.csv", "r") as currency_data:
            table = csv.reader(currency_data)
            conversions = {}
            for row in table:
                date = row[0]
                close = row[4]
                conversions[date] = close
            for i in historic_data:
                if i["high"] != 0 and i["low"] != 0 and i["close"]!= 0:
                    if i["date"] in conversions.keys():
                        converted_high = round(
                            float(conversions[i["date"]])*float(i["high"]), 2)
                        converted_low = round(
                            float(conversions[i["date"]])*float(i["low"]), 2)
                        converted_close = round(
                            float(conversions[i["date"]])*float(i["close"]), 2)
                        self.days.append(Day(i["date"], converted_high, converted_low, converted_close, i["volume"]))


            for i in dividend_data:
                if dividend_data[i]["date"] in conversions.keys():
                    converted_value = round(
                        float(conversions[dividend_data[i]["date"]])*float(dividend_data[i]["value"]), 2)
                    year = dividend_data[i]["date"][0:4]
                    if year not in self.dividends.keys():
                            self.dividends[year] = [{"date": dividend_data[i]["date"], "value": converted_value}]
                    else:
                        self.dividends[year].append({"date": dividend_data[i]["date"], "value": converted_value})

    def convert_ils(self, historic_data, dividend_data):
        with open(f"currencies/foreign-eur/ILS.FOREX.csv", "r") as currency_data:
            ils_table = csv.reader(currency_data)
            conversions_ils = {}
            for row in ils_table:
                date = row[0]
                close = row[4]
                conversions_ils[date] = close
            for i in historic_data:
                if i["date"] in conversions_ils.keys():
                    if i["high"] != 0 and i["low"] != 0 and i["close"]!= 0:
                        converted_high = round(float(conversions_ils[i["date"]])*float(i["high"]), 2)
                        converted_low = round(float(conversions_ils[i["date"]])*float(i["low"]), 2)
                        converted_close = round(float(conversions_ils[i["date"]])*float(i["close"]), 2)
                        with open(f"currencies/foreign-eur/USDEUR.FOREX.csv", "r") as us_currency_data:
                            usd_table = csv.reader(us_currency_data)
                            conversions_usd = {}
                            for row in usd_table:
                                date = row[0]
                                close = row[4]
                                conversions_usd[date] = close
                            final_converted_high = round(float(conversions_usd[i["date"]])*float(converted_high), 2)
                            final_converted_low = round(float(conversions_usd[i["date"]])*float(converted_low), 2)
                            final_converted_close = round(float(conversions_usd[i["date"]])*float(converted_close), 2)
                            self.days.append(Day(i["date"], final_converted_high, final_converted_low, final_converted_close, i["volume"]))

            for i in dividend_data:
                if dividend_data[i]["date"] in conversions_ils.keys():
                    converted_value = round(
                        float(conversions_ils[dividend_data[i]["date"]])*float(dividend_data[i]["value"]), 2)
                    with open(f"currencies/foreign-eur/USDEUR.FOREX.csv", "r") as us_currency_data:
                        usd_table = csv.reader(us_currency_data)
                        conversions_usd = {}
                        for row in usd_table:
                            date = row[0]
                            close = row[4]
                            conversions_usd[date] = close
                        final_converted_value = round(float(conversions_usd[dividend_data[i]["date"]])*float(converted_value), 2)
                        year = dividend_data[i]["date"][0:4]
                        if year not in self.dividends.keys():
                            self.dividends[year] = [{"date": dividend_data[i]["date"], "value": final_converted_value}]
                        else:
                            self.dividends[year].append({"date": dividend_data[i]["date"], "value": final_converted_value})


    def currency_conversion(self, historic_data, dividend_data):
        if self.currency != "EUR" and self.currency != "ILS":
            self.convert_other_currency(historic_data, dividend_data)
        if self.currency == "ILS":
            pass
            #self.convert_ils(historic_data, dividend_data)
        if self.currency == "EUR":
            for i in historic_data:
                if i["high"] != 0 and i["low"] != 0 and i["close"]!= 0:
                    self.days.append(
                        Day(i["date"], i["high"], i["low"], i["close"], i["volume"]))
            for i in dividend_data:
                year = dividend_data[i]["date"][0:4]
                if year not in self.dividends.keys():
                    self.dividends[year] = [{"date": dividend_data[i]["date"], "value": dividend_data[i]["value"]}]
                else:
                    self.dividends[year].append({"date": dividend_data[i]["date"], "value": dividend_data[i]["value"]})

    def get_day_by_date(self, date):
        for index in range(len(self.days)):
            if self.days[index].date == date:
                return self.days[index]
        return "pop"


def write_dividends_to_db(name, dividends):
    db_connection = sqlite3.connect('databases/div_trade_v9c-SWE2.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT ID FROM '01_Companies' WHERE Name = '{name}'")
    company_id = db_cursor.fetchone()
    company_id = company_id[0]
    for year in dividends.keys():
        for i in range(len(dividends[year])):
            try:
                db_cursor.execute(f"""INSERT INTO 'dividends_{year}' ('Company_ID', 'Index', 'Date', 'Amount', 'Percent') 
                            VALUES ('{company_id}','{i}','{dividends[year][i]["date"]}','{dividends[year][i]["value"]}','{dividends[year][i]["percent"]}')""")
            except KeyError:
                pass
    db_connection.commit()
    db_cursor.close()
    print(f"{name} dividends added")

def write_historic_data_to_db(ticker, days):
    db_connection = sqlite3.connect('databases/div_trade_v9c-SWE2.db')
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute(f"""CREATE TABLE "{ticker}" 
                        ("ID" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "Date" TEXT NOT NULL,
                        "High" INTEGER NOT NULL,
                        "Low" INTEGER NOT NULL,
                        "Close" INTEGER NOT NULL,
                        "Volume" INTEGER)""")
    except sqlite3.OperationalError:
        pass
    db_connection.commit()
    for day in days:
        db_cursor.execute(f"INSERT INTO '{ticker}' (Date, High, Low, Close, Volume) VALUES ('{day.date}','{day.high}','{day.low}','{day.close}','{day.volume}')")
    db_connection.commit()
    db_cursor.close()
    print(f"{ticker} table added")

def write_company_to_db(name, ticker, currency):
    print(ticker)
    db_connection = sqlite3.connect('databases/div_trade_v9c-SWE2.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(
        f"SELECT Name FROM '01_Companies' WHERE Name = '{name}'")
    company = db_cursor.fetchone()
    if not company:
        db_cursor.execute(
            f"INSERT INTO '01_Companies' (Name, Ticker, Currency) VALUES ('{name}', '{ticker}','{currency}')")
        db_connection.commit()
        db_cursor.close()
        print(f"{ticker} added to companies")
        return True
    else:
        print(company)
        db_cursor.close()
        return False

def initial_filter(historic_data, dividend_data, company):
    if type(dividend_data) != dict:
        print("dict")
        return False
    try:
        x = float(historic_data[-1]["close"])*0.5
    except TypeError:
        print("historic")
        return False
    try:
        y = float(dividend_data["1"]["value"])*0.5
    except TypeError:
        print("dividend")
        return False
    except KeyError:
        print(dividend_data)
        return False
    if company.currency == "USD" or company.currency == "CAD":
        if len(dividend_data.keys()) < 20:
            print("not enough dividends")
            return False
    if len(dividend_data.keys()) < 5:
        print("not enough dividends")
        return False
    for i in historic_data:
        if type(i) != dict:
            print("historic i not dict")
            return False
    else:
        return True

def get_historic_data(ticker, api_token, params):
    session = requests.Session()
    url_historic = f"https://eodhistoricaldata.com/api/eod/{ticker}?api_token={api_token}&fmt=json"
    reponse_historic = session.get(url_historic, params=params)
    if reponse_historic.status_code == requests.codes.ok:
        historic_data = json.loads(reponse_historic.text)
        return historic_data
    else:
        print(f"{ticker} historic status problem")


def get_dividend_data(ticker, api_token, params):
    session = requests.Session()
    url_dividends = f"https://eodhistoricaldata.com/api/div/{ticker}?api_token={api_token}&from=2000-01-01&fmt=json"
    reponse_dividends = session.get(url_dividends, params=params)
    if reponse_dividends.status_code == requests.codes.ok:
        dividend_data = json.loads(reponse_dividends.text)
        return dividend_data
    else:
        print(f"{ticker} dividend status problem")

def get_eod_data(eod_ticker, api_token):
    params = {"api_token": api_token}
    historic_data = get_historic_data(eod_ticker, api_token, params)
    dividend_data = get_dividend_data(eod_ticker, api_token, params)
    return historic_data, dividend_data

def get_ticker(api_token):
    exchange_codes={"US":"US",} #done: ("SWE":"ST","AT":"VI","GER":"XETRA","DEN":"CO","CHF":"VX","NOR":"OL","FR":"PA","SP":"MC","IT":"MI","CA":"TO","UK":"LSE") /to_do: ,
    session = requests.Session()
    params = {"api_token": api_token}
    companies = {}
    for key in exchange_codes.keys():
        print(f"geting ticker from {exchange_codes[key]}")
        url_exchange= f"https://eodhistoricaldata.com/api/exchanges/{exchange_codes[key]}?api_token={api_token}&fmt=json"
        reponse_exchange = session.get(url_exchange, params=params)
        if reponse_exchange.status_code == requests.codes.ok:
            print("status ok")
            exchange_data = json.loads(reponse_exchange.text)
            for item in exchange_data:
                currency = item["Currency"]
                if currency == "GBX":
                    currency = "GBP"
                exchange = item["Exchange"]
                if currency == "USD":
                    exchange = "US"
                db_ticker = item["Code"]
                ticker = f"{db_ticker}.{exchange}"
                if item["Type"] == "Common Stock" and ticker not in companies.keys():
                    name = item["Name"]
                    if name != None:
                        if "'" in name:
                            name = name.replace("'", "")
                        company = Company(name, ticker, exchange, currency)
                        companies[ticker] = company
    return companies

def get_bans():
    db_connection = sqlite3.connect('./databases/div_trade_v9c-SWE2.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Ticker FROM '01_Companies' WHERE Currency = 'USD'")
    db_ticker = db_cursor.fetchall()
    bans = []
    for ticker in db_ticker:
        bans.append(ticker[0])
    db_connection.close()
    return bans

if __name__ == "__main__":
    api_token = "5d19ac0dbbdd85.51123060"
    companies = get_ticker(api_token)
    print(len(companies))
    #bans = get_bans()
    bans = []
    print(len(bans))
    counter = 0
    for key in companies.keys():   
        counter +=1
        if key in bans:
            pass
        if key not in bans:
            company=companies[key]
            historic_data, dividend_data = get_eod_data(key, api_token)
            #print(dividend_data)
            if initial_filter(historic_data, dividend_data, company):
                company.currency_conversion(historic_data, dividend_data)
                print("currency_conversion done")
                for year in company.dividends.keys():
                    for n in range(len(company.dividends[year])):
                        company.calculate_dividend_percentage(year, n)

                if write_company_to_db(company.name, company.ticker, company.currency):
                    write_historic_data_to_db(company.ticker, company.days)
                    write_dividends_to_db(company.name, company.dividends)
            if counter == 2000:
                time.sleep(120)
                counter = 0

                




