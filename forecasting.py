import requests
import json
import time
import sqlite3
import v2_packages as packages
from datetime import date, timedelta

class Trade:
    def __init__(self, buy_date, sell_date, buy_high, buy_low, sell_high,sell_low):
        self.buy_date = buy_date
        self.sell_date = sell_date
        self.buy_high= round(buy_high,2)
        self.buy_low= round(buy_low,2)
        self.sell_high= round(sell_high,2)
        self.sell_low= round(sell_low,2)
        self.high_return = {}
        self.low_return = {}
        self.average_return = {}

    def calc_returns(self, buy_price, sell_price, dividend_amount):
        return_amount = sell_price + dividend_amount - buy_price
        return_percent = round((return_amount/buy_price)*100,2)
        return_amount = round(return_amount,2)
        return return_amount, return_percent

    def add_returns(self, dividend_amount):
        high_amount, high_percent = self.calc_returns(self.buy_low, self.sell_high, dividend_amount)
        low_amount, low_percent = self.calc_returns(self.buy_high, self.sell_low, dividend_amount)
        self.high_return = {"amount":high_amount,"percent":high_percent}
        self.low_return = {"amount":low_amount,"percent":low_percent}
        average_amount = round((self.low_return["amount"]+self.high_return["amount"])/2,2)
        average_percent = round((self.low_return["percent"]+self.high_return["percent"])/2,2)
        self.average_return = {"amount":average_amount,"percent":average_percent}

class Company:
    def __init__(self, ticker, name, company_id, forecast_date, buy_date, sell_date):
        self.ticker = ticker
        self.name = name
        self.id = company_id
        self.forecast_date = forecast_date
        self.buy_date = buy_date
        self.sell_date = sell_date
        self.trades = {}
        self.dividends = {}
        self.trends200 = {}
        self.average_returns = {}
        self.median_returns = {}
        self.bad_trades = {}
        self.severe_trades = {}
        self.great_trades = {}
        self.strikes = {}
        self.ranking_points = {}

    def add_dividend_values(self, year,date, amount, percent):
        self.dividends[year] = {"date":date,"amount":amount,"percent":percent}

    def add_trend200(self, year, ticker, buy_index, buy_close, db_connection, db_cursor):
        start_index = buy_index-200
        if start_index < 1:
            start_index = 1
        db_cursor.execute(f"SELECT Close FROM '{ticker}' WHERE ID < {buy_index} AND ID > {start_index}")
        close_prices = db_cursor.fetchall()
        # if trend200 > 1 positive trend, if trend200 < 1 negative trend
        sum_close = 0
        for close_price in close_prices:
            sum_close += close_price[0]
        if buy_index == 1:
            trend200 = round(buy_close/1,2)
        else:
            try:
                trend200 = round(buy_close/(sum_close/len(close_prices)),2)
                self.trends200[year] = trend200
            except ZeroDivisionError:
                print(year, ticker, buy_index, buy_close, close_prices, sum_close)

    def get_buy_sell_values(self, ticker, dividend_date, db_connection, db_cursor, timeframe_buy, timeframe_sell):
        db_cursor.execute(f"SELECT * FROM '{ticker}' WHERE ID = (SELECT ID FROM '{ticker}' WHERE DATE = '{dividend_date}')-{timeframe_buy}") 
        buy_values = db_cursor.fetchall()
        db_cursor.execute(f"SELECT * FROM '{ticker}' WHERE ID = (SELECT ID FROM '{ticker}' WHERE DATE = '{dividend_date}')+{timeframe_sell}")
        sell_values = db_cursor.fetchall()
        return buy_values, sell_values

    def add_trade(self, year, ticker, dividend_date, dividend_amount, db_connection, db_cursor, timeframe_buy, timeframe_sell):   
        buy_values, sell_values = self.get_buy_sell_values(ticker, dividend_date, db_connection, db_cursor, timeframe_buy, timeframe_sell)
        try:
            self.trades[year]=Trade(buy_values[0][1],sell_values[0][1],buy_values[0][2],buy_values[0][3],sell_values[0][2],sell_values[0][3])
            self.trades[year].add_returns(dividend_amount)
            self.add_trend200(year, ticker, buy_values[0][0], buy_values[0][4], db_connection, db_cursor)
            return True
        except IndexError:
            #print(dividend_date)
            #print(IndexError, ticker, year, buy_values, sell_values)
            return False
        

    def calc_average(self, year):
        sum_average_percent = 0
        length_counter = 0
        for key in self.trades.keys():
            if key <= year:
                sum_average_percent += self.trades[key].average_return["percent"]
                length_counter += 1
        try:
            self.average_returns[year] = round(sum_average_percent/length_counter,2)
        except ZeroDivisionError:
            print(self.ticker, year, self.trades.keys(),length_counter)

    def calc_median(self, year):
        return_percents = []
        for key in self.trades.keys():
            if key <= year:
                return_percents.append(self.trades[key].average_return["percent"])
        sorted_returns = sorted(return_percents)
        self.median_returns[year] = sorted_returns[int(len(sorted_returns)/2)]

    def assess_trades(self, year):
        length_counter = 0
        bad_trades = 0
        severe_trades = 0
        great_trades = 0
        for key in self.trades.keys():
            if key <= year:
                if self.trades[key].average_return["percent"] < 0:
                    bad_trades += 1
                    length_counter += 1
                if self.trades[key].average_return["percent"] < -5:
                    severe_trades += 1
                    length_counter += 1
                if self.trades[key].average_return["percent"] > 10:
                    great_trades += 1
                    length_counter += 1
        if bad_trades == 0:
            self.bad_trades[year] = 0
        else:
            self.bad_trades[year] = round((bad_trades/length_counter)*100,2)
        if severe_trades == 0:
            self.severe_trades[year] = 0
        else:
            self.severe_trades[year] = round((severe_trades/length_counter)*100,2)
        if great_trades == 0:
            self.great_trades[year] = 0
        else:
            self.great_trades[year] = round((great_trades/length_counter)*100,2)

    def calc_strikes(self, year, form_data):
        strikes = 0
        if self.average_returns[year] < form_data["average_threshold"]:
            strikes += form_data["average_strikes"]
        if self.median_returns[year] < form_data["median_threshold"]:
            strikes += form_data["median_strikes"]
        if self.bad_trades[year] > form_data["bad_trades_threshold"]:
            strikes += form_data["bad_trades_strikes"]
        if self.bad_trades[year] > form_data["bad_trades2_threshold"]:
            strikes += form_data["bad_trades2_strikes"]
        if self.severe_trades[year] > form_data["severe_trades_threshold"]:
            strikes += form_data["severe_trades_strikes"]
        if self.great_trades[year] < form_data["great_trades_threshold"]:
            strikes += form_data["great_trades_strikes"]
        self.strikes[year] = strikes

    def add_ranking_points(self, year, points):
        self.ranking_points[year] = points

class Companies:
    def __init__(self):
        self.companies = {}
    
    def add_company(self, ID, company):
        self.companies[ID] = company

    def check_last_five_years(self, ID):
        last_five_years = [2014, 2015, 2016, 2017, 2018]
        for year in last_five_years:
            if year not in self.companies[ID].trades.keys() and year not in self.companies[ID].ranking_points.keys():
                return False
        return True


    def fill_companies(self, db_connection, db_cursor, company_infos, timeframe_buy, timeframe_sell, form_data, input_year):
        years = [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018] #2000, 2001, 2002, 2003, 2004, 2005, 2006, 
        for year in years:
            print(year)
            db_cursor.execute(f"SELECT * FROM 'dividends_{year}'")
            dividends_data = db_cursor.fetchall()
            for row in dividends_data:
                if row[1] in company_infos.keys():
                    ticker = company_infos[row[1]]["ticker"]
                    ID = f"{ticker}"
                    if ID in self.companies.keys():   
                        if self.companies[ID].add_trade(year, company_infos[row[1]]["ticker"], row[3],row[4], db_connection, db_cursor, timeframe_buy, timeframe_sell):
                            self.companies[ID].add_dividend_values(year, row[3],row[4],row[5])
                    else:
                        new_company = Company(company_infos[row[1]]["ticker"],company_infos[row[1]]["name"],row[1], company_infos[row[1]]["hv_date"], 
                        company_infos[row[1]]["buy_date"], company_infos[row[1]]["sell_date"])
                        self.add_company(ID, new_company)
                        if self.companies[ID].add_trade(year, company_infos[row[1]]["ticker"], row[3],row[4], db_connection, db_cursor, timeframe_buy, timeframe_sell):
                            self.companies[ID].add_dividend_values(year, row[3],row[4],row[5])
        
        for ID in self.companies.keys():
            if self.check_last_five_years(ID):
                self.companies[ID].calc_average(input_year-1)
                self.companies[ID].calc_median(input_year-1)
                self.companies[ID].assess_trades(input_year-1)
                self.companies[ID].calc_strikes(input_year-1, form_data)
                        


def calc_indicator(year, companies, form_data):
    averages_rank = []
    medians_rank = []
    bad_trades_rank = []
    severe_trades_rank = []
    great_trades_rank = []
    for key in companies.keys():
        averages_rank.append((companies[key].average_returns[year], key))
        medians_rank.append((companies[key].median_returns[year], key))
        bad_trades_rank.append((companies[key].bad_trades[year], key))
        severe_trades_rank.append((companies[key].severe_trades[year], key))
        great_trades_rank.append((companies[key].great_trades[year], key))

    averages_rank.sort()
    medians_rank.sort()
    bad_trades_rank.sort()
    bad_trades_rank.reverse()
    severe_trades_rank.sort()
    bad_trades_rank.reverse()
    great_trades_rank.sort()

    for key in companies.keys():
        points = 0
        for n in range(len(averages_rank)):
            if key in averages_rank[n]:
                points += n * (form_data["averages_multiplier"]/100)
            if key in medians_rank[n]:
                points += n * (form_data["medians_multiplier"]/100)
            if key in bad_trades_rank[n]:
                points += n * (form_data["bad_trades_multiplier"]/100)
            if key in severe_trades_rank[n]:
                points += n * (form_data["severe_trades_multiplier"]/100)
            if key in great_trades_rank[n]:
                points += n * (form_data["great_trades_multiplier"]/100)
        companies[key].add_ranking_points(year, points)

def filter_company(year, company):
    try:
        if company.strikes[year] < 1: #10
            return False
    except KeyError:
        return False
    if company.dividends[year]["percent"] > 30:
        return False
    if company.bad_trades[year] > 90: #50
        return False
    if company.severe_trades[year] > 90: #10
        return False
    if company.average_returns[year] < 2:
        return False
    if company.median_returns[year] < 0:
        return False
    if company.trades[year].buy_date == None:
        return False
    else:
        return True

def calculate_buy_and_sell_date(hv_date, timeframe_buy, timeframe_sell):
    hv_split = hv_date.split("-")
    datetime_hv = date(int(hv_split[0]),int(hv_split[1]),int(hv_split[2]))
    print(datetime_hv)
    buy_date = datetime_hv - timedelta(days=timeframe_buy)
    print(buy_date, timeframe_buy)
    print(datetime_hv)
    sell_date = datetime_hv - timedelta(days=-timeframe_sell)
    print(sell_date, timeframe_sell)
    return buy_date, sell_date

def webcall(form_data):
    timeframe_buy = int(form_data["timeframe_buy"])
    timeframe_sell = int(form_data["timeframe_sell"])
    timeframe = f"{timeframe_buy}-{timeframe_sell}"
    print(timeframe)

    db_connection = sqlite3.connect('./databases/div_trade_v9.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT * FROM '01_Companies'")
    db_company_infos = db_cursor.fetchall()

    api_token = "5d19ac0dbbdd85.51123060"   
    params = {"api_token": api_token}  
    session = requests.Session()
    start_date = form_data["start_date"]
    input_year = int(start_date[0:4])
    url_forecasting = f"https://eodhistoricaldata.com/api/calendar/earnings?api_token={api_token}&from={start_date}&to={input_year}-12-31&fmt=json"
    reponse_forecasting = session.get(url_forecasting, params=params)

    forecasting_eod_ticker = []
    forecasting_ticker = {}
    company_infos = {}

    if reponse_forecasting.status_code == requests.codes.ok:
        forecasting_data = json.loads(reponse_forecasting.text)
        #print(forecasting_data)
        for element in forecasting_data["earnings"]:
            forecasting_eod_ticker.append(element["code"])
            ticker = element["code"][:element["code"].index(".")]
            forecasting_ticker[ticker] = element["report_date"]

        for row in db_company_infos:
            if row[3] != "US":
                if row[2] in forecasting_ticker.keys():
                    buy_date, sell_date = calculate_buy_and_sell_date(forecasting_ticker[row[2]], timeframe_buy, timeframe_sell)
                    company_infos[row[0]] = {"name":row[1],"exchange":row[3],"currency":row[4],"ticker":row[2], "hv_date":forecasting_ticker[row[2]]
            ,"buy_date":buy_date,"sell_date":sell_date}

        all_companies = Companies()
        filtered_companies = {}
        
        all_companies.fill_companies(db_connection, db_cursor, company_infos, timeframe_buy, timeframe_sell, form_data, input_year)
        for key in all_companies.companies.keys():
            if filter_company(input_year-1, all_companies.companies[key]):
                filtered_companies[key] = (all_companies.companies[key])
        print("indicator")
        calc_indicator(input_year-1, filtered_companies, form_data)
        starte_date_split=start_date.split("-")
        datetime_start_date = date(int(starte_date_split[0]),int(starte_date_split[1]),int(starte_date_split[2]))
        best_package = packages.get_forecasting_companies(filtered_companies, input_year-1, datetime_start_date)
        return best_package