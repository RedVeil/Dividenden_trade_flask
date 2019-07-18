import sqlite3
import v2_packages as packages
import v2_backtest as backtest

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
    def __init__(self, ticker, name, company_id):
        self.ticker = ticker
        self.name = name
        self.id = company_id
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
        self.average_returns[year] = round(sum_average_percent/length_counter,2)

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

    def calc_strikes(self, year):
        strikes = 0
        if self.average_returns[year] < 2:
            strikes += 1
        if self.median_returns[year] < 2:
            strikes += 1
        if self.bad_trades[year] > 10:
            strikes += 2
        if self.bad_trades[year] > 20:
            strikes += 4
        if self.severe_trades[year] > 10:
            strikes += 5
        if self.great_trades[year] < 5:
            strikes += 1
        self.strikes[year] = strikes

    def add_ranking_points(self, year, points):
        self.ranking_points[year] = points

class Companies:
    def __init__(self):
        self.companies = {}
    
    def add_company(self, ID, company):
        self.companies[ID] = company

    def fill_companies(self,year, db_connection, db_cursor, company_infos, timeframe_buy, timeframe_sell):
        db_cursor.execute(f"SELECT * FROM 'dividends_{year}' WHERE Company_ID=1")
        dividends_data = db_cursor.fetchall()
        for row in dividends_data:
            if row[1] < 2410:
                ticker = company_infos[row[1]]["ticker"]
                ID = f"{ticker}-{row[2]}"
                if ID in self.companies.keys():   
                    if self.companies[ID].add_trade(year, company_infos[row[1]]["ticker"], row[3],row[4], db_connection, db_cursor, timeframe_buy, timeframe_sell):
                        self.companies[ID].add_dividend_values(year, row[3],row[4],row[5])
                        self.companies[ID].calc_average(year)
                        self.companies[ID].calc_median(year)
                        self.companies[ID].assess_trades(year)
                        self.companies[ID].calc_strikes(year)
                else:
                    new_company = Company(company_infos[row[1]]["ticker"],company_infos[row[1]]["name"],row[1])
                    self.add_company(ID, new_company)
                    if self.companies[ID].add_trade(year, company_infos[row[1]]["ticker"], row[3],row[4], db_connection, db_cursor, timeframe_buy, timeframe_sell):
                        self.companies[ID].add_dividend_values(year, row[3],row[4],row[5])
                        self.companies[ID].calc_average(year)
                        self.companies[ID].calc_median(year)
                        self.companies[ID].assess_trades(year)
                        self.companies[ID].calc_strikes(year)


def calc_indicator(year, companies):
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
                points += n * (100/100)
            if key in medians_rank[n]:
                points += n * (100/100)
            if key in bad_trades_rank[n]:
                points += n * (100/100)
            if key in severe_trades_rank[n]:
                points += n * (100/100)
            if key in great_trades_rank[n]:
                points += n * (100/100)
        companies[key].add_ranking_points(year, points)

def filter_company(year, years, company, key):
    try:
        if company.strikes[year] < 10: #10
            return False
    except KeyError:
        return False
    if year not in company.trades.keys():
        return False
    if company.dividends[year]["percent"] > 30:
        return False
    if company.bad_trades[year] > 50: #50
        return False
    if company.severe_trades[year] > 10: #10
        return False
    if company.average_returns[year] < 2:
        return False
    if company.median_returns[year] < 0:
        return False
    if company.trades[year].buy_date == None:
        return False
    if year != years[0]:
        if year-1 not in company.trades.keys() or year-1 not in company.ranking_points.keys():
            return False
        else:
            return True
    else:
        return True


def webcall():
    total_years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008,
                   2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    years = total_years[8:10]
    timeframe_buy = 10
    timeframe_sell = 5
    timeframe = f"{timeframe_buy}-{timeframe_sell}"
    print(timeframe)
    db_connection = sqlite3.connect('./databases/div_trade_v9.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT * FROM '01_Companies' WHERE Ticker = '2FI'")
    db_company_infos = db_cursor.fetchall()
    company_infos = {}
    for row in db_company_infos:
        if row[3] != "US":
            print(row[1], row[3], row[4], row[2])
            company_infos[row[0]] = {"name":row[1],"exchange":row[3],"currency":row[4],"ticker":row[2]}
    all_companies = Companies()
    filtered_companies = {}
    last_date = ""
    tax_credit_high = 0
    tax_credit_low = 0
    backtest_breackdowns = {}
    for year in years:
        print(year)
        all_companies.fill_companies(year, db_connection, db_cursor, company_infos, timeframe_buy, timeframe_sell)
        print(all_companies.companies["2FI-0"].ticker)
        print(all_companies.companies["2FI-0"].name)
        print(all_companies.companies["2FI-0"].id)
        print(all_companies.companies["2FI-0"].trades[year].buy_date,all_companies.companies["2FI-0"].trades[year].sell_date,all_companies.companies["2FI-0"].trades[year].buy_high,all_companies.companies["2FI-0"].trades[year].buy_low,all_companies.companies["2FI-0"].trades[year].sell_high,all_companies.companies["2FI-0"].trades[year].sell_low)
        print(all_companies.companies["2FI-0"].dividends[year])
        print(all_companies.companies["2FI-0"].trends200[year])
        print(all_companies.companies["2FI-0"].average_returns[year])
        print(all_companies.companies["2FI-0"].median_returns[year])
        print(all_companies.companies["2FI-0"].bad_trades[year])
        print(all_companies.companies["2FI-0"].severe_trades[year])
        print(all_companies.companies["2FI-0"].great_trades[year])
        print(all_companies.companies["2FI-0"].strikes[year])
        for key in all_companies.companies.keys():
            if filter_company(year, years, all_companies.companies[key], key):
                filtered_companies[key] = (all_companies.companies[key])
        calc_indicator(year, filtered_companies)
        print(all_companies.companies["2FI-0"].ranking_points[year])
        """if year == years[1]:
            best_package = packages.get_companies(filtered_companies, year)
            last_date, amount_high, amount_low, tax_credit_high, tax_credit_low, backtest_breackdown = backtest.backtesting(timeframe, best_package, amount_high, amount_low, tax_credit_high, tax_credit_low)
            backtest_breackdowns[year] = backtest_breackdown
        if year > years[1]:
            best_package = packages.get_companies(filtered_companies, year, last_date)
            last_date, amount_high, amount_low, tax_credit_high, tax_credit_low, backtest_breackdown = backtest.backtesting(
                timeframe, best_package, amount_high, amount_low, tax_credit_high, tax_credit_low)
            backtest_breackdowns[year] = backtest_breackdown
        filtered_companies = {}
    return backtest_breackdowns"""
webcall()