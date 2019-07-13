import requests
import csv
import sqlite3
import json


class Day:
    def __init__(self, date, high, low, close):
        self.date = date
        self.high = float(high)
        self.low = float(low)
        self.average = round((self.high + self.low)/2, 2)
        self.close = (float(close))


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
    def __init__(self, name, ticker, exchange, currency):
        self.name = name
        self.ticker = ticker
        self.currency = currency
        self.exchange = exchange
        self.scenarios = {}
        self.days = []
        self.dividends = []

    def fill_tables(self, year, hv):
        hv_date = hv["date"]
        print(hv_date)
        db_connection = sqlite3.connect('databases/div_trade_v8.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(
            f"SELECT ID FROM Companies WHERE Company = '{self.name}'")
        company_id = db_cursor.fetchone()
        company_id = company_id[0]
        for i in self.scenarios[hv_date]:
            db_cursor.execute(f"""INSERT INTO '{year}' ('Company_ID', 'Timeframe_Buy','Timeframe_Sell','High_%','Avg_%','Low_%', 'Dividend_%','Dividends','Day_Line200', 'Buy_Date', 'Sell_Date',
                            'Buy_High', 'Buy_Low', 'Sell_High', 'Sell_Low') 
                            VALUES ('{company_id}', '{i.timeframe_buy}','{i.timeframe_sell}',{i.best_percent},{i.medium_percent},{i.worst_percent}, {hv["percentage"]} , {i.dividend}, 0,
                            '{i.buy_date}', '{i.sell_date}',
                            {i.buy_high},{i.buy_low},{i.sell_high},{i.sell_low})""")
        db_connection.commit()
        db_cursor.close()
        print(f"{year} tables filled")

    def write_hv_to_db(self, hv):
        db_connection = sqlite3.connect('databases/div_trade_v8.db')
        db_cursor = db_connection.cursor()
        year = str(hv["date"])[0:4]
        db_cursor.execute(
            f"SELECT Company FROM Companies WHERE Company = '{self.name}'")
        company = db_cursor.fetchone()
        if not company:
            db_cursor.execute(
                f"INSERT INTO Companies (Company, Exchange, Years, Currency, Ticker) VALUES ('{self.name}', '{self.exchange}', 0, '{self.currency}', '{self.ticker}')")
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
        except sqlite3.OperationalError:
            pass
        db_connection.commit()
        db_cursor.close()
        self.fill_tables(year, hv)

    def add_scenario(self, scenario, date):
        if date not in self.scenarios.keys():
            self.scenarios[date] = [scenario]
        else:
            self.scenarios[date].append(scenario)

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

    def calculate_dividend_percentage(self, dividend_value, dividend_date, ex_day):
        dividend_percentage = round(dividend_value/ex_day.close*100, 2)
        for index in range(len(self.dividends)):
            if self.dividends[index]["date"] == dividend_date:
                self.dividends[index]["percentage"] = dividend_percentage

    def convert_other_currency(self, historic_data, dividend_data):
        with open(f"currencies/foreign-eur/{self.currency}EUR.FOREX.csv", "r") as currency_data:
            table = csv.reader(currency_data)
            conversions = {}
            for row in table:
                date = row[0]
                close = row[4]
                conversions[date] = close
            for i in historic_data:
                if i["date"] in conversions.keys():
                    converted_high = round(
                        float(conversions[i["date"]])*float(i["high"]), 2)
                    converted_low = round(
                        float(conversions[i["date"]])*float(i["low"]), 2)
                    converted_close = round(
                        float(conversions[i["date"]])*float(i["close"]), 2)
                    self.days.append(Day(i["date"], converted_high, converted_low, converted_close))


            for i in dividend_data:
                if dividend_data[i]["date"] in conversions.keys():
                    converted_value = round(
                        float(conversions[dividend_data[i]["date"]])*float(dividend_data[i]["value"]), 2)
                    self.dividends.append({"date": dividend_data[i]["date"], "value": converted_value})

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
                        self.days.append(Day(i["date"], final_converted_high, final_converted_low, final_converted_close))

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
                        self.dividends.append({"date": dividend_data[i]["date"], "value": final_converted_value})


    def currency_conversion(self, historic_data, dividend_data):
        if self.currency != "EUR" and self.currency != "ILS":
            self.convert_other_currency(historic_data, dividend_data)
        if self.currency == "ILS":
            pass
            #self.convert_ils(historic_data, dividend_data)
        if self.currency == "EUR":
            for i in historic_data:
                self.days.append(
                    Day(i["date"], i["high"], i["low"], i["close"]))
            for i in dividend_data:
                self.dividends.append(
                    {"date": dividend_data[i]["date"], "value": dividend_data[i]["value"]})

    def get_day_by_date(self, date):
        for index in range(len(self.days)):
            if self.days[index].date == date:
                return self.days[index], index

    def calc_scenario(self, hv, timeframe_buy, timeframe_sell):
        ex_day, index = self.get_day_by_date(hv["date"])
        self.calculate_dividend_percentage(hv["value"], hv["date"], ex_day)
        buy_high, buy_average, buy_low, buy_date = self.get_buy_prices(
            index, timeframe_buy)
        sell_high, sell_average, sell_low, sell_date = self.get_sell_prices(
            index, timeframe_sell)
        scenario = Scenario(buy_high, buy_average, buy_low, sell_high, sell_average,
                            sell_low, hv["value"], buy_date, sell_date, timeframe_buy, timeframe_sell)
        self.add_scenario(scenario, hv["date"])


def initial_filter(historic_data, dividend_data, company):
    if type(dividend_data) != dict:
        return False
    try:
        x = float(historic_data[-1]["close"])*0.5
    except TypeError:
        return False
    try:
        y = float(dividend_data["1"]["value"])*0.5
    except TypeError:
        return False
    except KeyError:
        print(dividend_data)
    if company.currency == "BRL":
        if historic_data[-1]["close"]*0.2315 < 8:
            return False
    if company.currency == "CAD":
        if historic_data[-1]["close"]*0.6813 < 8:
            return False
    if company.currency == "CHF":
        if historic_data[-1]["close"]*0.8986< 8:
            return False
    if company.currency == "CZK":
        if historic_data[-1]["close"]*0.0393 < 8:
            return False
    if company.currency == "DKK":
        if historic_data[-1]["close"]*0.134 < 8:
            return False
    if company.currency == "GBP":
        if historic_data[-1]["close"]*1.1147 < 8:
            return False
    if company.currency == "ILS":
        if historic_data[-1]["close"]*0.25 < 8:
            return False
    if company.currency == "INR":
        if historic_data[-1]["close"]*0.0129 < 8:
            return False
    if company.currency == "NOK":
        if historic_data[-1]["close"]*0.1037 < 8:
            return False
    if company.currency == "PLN":
        if historic_data[-1]["close"]*0.2358 < 8:
            return False
    if company.currency == "SEK":
        if historic_data[-1]["close"]*0.095 < 8:
            return False
    if company.currency == "USD":
        if historic_data[-1]["close"]*0.8926 < 8:
            return False
    if company.currency == "ZAR":
        if historic_data[-1]["close"]*0.0628 < 8:
            return False
    if company.currency == "EUR":
        if historic_data[-1]["close"] < 8:
            return False
    if company.currency == "USD" or company.currency == "CAD":
        if len(dividend_data.keys()) < 32:
            return False
    if len(dividend_data.keys()) < 8:
        return False
    for i in historic_data:
        if type(i) != dict:
            return False



def get_historic_data(ticker, api_token, params):
    session = requests.Session()
    url_historic = f"https://eodhistoricaldata.com/api/eod/{ticker}?api_token={api_token}&fmt=json"
    reponse_historic = session.get(url_historic, params=params)
    if reponse_historic.status_code == requests.codes.ok:
        historic_data = json.loads(reponse_historic.text)
        return historic_data


def get_dividend_data(ticker, api_token, params):
    session = requests.Session()
    url_dividends = f"https://eodhistoricaldata.com/api/div/{ticker}?api_token={api_token}&from=2000-01-01&fmt=json"
    reponse_dividends = session.get(url_dividends, params=params)
    if reponse_dividends.status_code == requests.codes.ok:
        dividend_data = json.loads(reponse_dividends.text)
        return dividend_data

def get_eod_data(eod_ticker, api_token):
    params = {"api_token": api_token}
    historic_data = get_historic_data(eod_ticker, api_token, params)
    dividend_data = get_dividend_data(eod_ticker, api_token, params)
    return historic_data, dividend_data

def create_timeframes():
    timeframes = {}
    timeframe_buy = 0  # Default 0
    while timeframe_buy < 60:  # Default 60
        timeframe_buy += 1
        for i in range(11):  # Default 11
            timeframe_sell = i
            timeframe = f"{timeframe_buy}-{timeframe_sell}"
            timeframes[timeframe] = [timeframe_buy, timeframe_sell]
    return timeframes


def get_ticker(api_token):
    exchange_codes={"GER":"XETRA", "LUX":"LU","AT":"VI","SP":"MC","FR":"PA","CHF":"VX","IT":"MI","SWE":"ST","NOR":"OL","DEN":"CO"} #"UK":"LSE", "US":"US","CA":"TO",
    session = requests.Session()
    params = {"api_token": api_token}
    companies = {}
    for key in exchange_codes.keys():
        print(f"geting ticker from {exchange_codes[key]}")
        url_exchange= f"https://eodhistoricaldata.com/api/exchanges/{exchange_codes[key]}?api_token={api_token}&fmt=json"
        reponse_exchange = session.get(url_exchange, params=params)
        if reponse_exchange.status_code == requests.codes.ok:
            exchange_data = json.loads(reponse_exchange.text)
            for item in exchange_data:
                if item["Type"] == "Common Stock" and item["Code"] not in companies.keys():
                    currency = item["Currency"]
                    if currency == "GBX":
                        currency = "GBP"
                    company = Company(item["Name"], item["Code"], item["Exchange"], currency)
                    companies[item["Code"]] = company
    return companies


if __name__ == "__main__":
    api_token = "5d19ac0dbbdd85.51123060"
    companies = get_ticker(api_token)
    timeframes = create_timeframes()
    for key in companies.keys():
        company=companies[key]
        eod_ticker = f"{company.ticker}.{company.exchange}"
        historic_data, dividend_data = get_eod_data(eod_ticker, api_token)
        if initial_filter(historic_data, dividend_data, company):
            print(company.name, company.currency, company.exchange)
            company.currency_conversion(historic_data, dividend_data)
            for hv in company.dividends:
                for timeframe in timeframes:
                    company.calc_scenario(
                        hv, timeframes[timeframe][0], timeframes[timeframe][1])
            company.write_hv_to_db(hv)
