import sqlite3
from datetime import date
import math
import time


class Backtest_Breakdown:
    def __init__(self, buy_date, sell_date, name,  ticker, timeframe, high, low, buy_high, buy_low, sell_high, sell_low, dividend_percent, dividend, day_line200):
        self.buy_date = buy_date
        self.sell_date = sell_date
        self.ticker = ticker
        self.name = name
        self.timeframe = timeframe
        self.dividend_percent = dividend_percent
        self.dividend = dividend
        self.day_line200 = day_line200
        self.start_amount_high = round(high,2)
        self.start_amount_low = round(low,2)
        self.unused_high = 0
        self.unused_low = 0
        self.stock_amount_high = 0
        self.stock_amount_low = 0
        self.buy_price_high = round(buy_high,2)
        self.buy_price_low = round(buy_low,2)
        self.sell_price_high = round(sell_high,2)
        self.sell_price_low = round(sell_low,2)
        self.return_high = 0
        self.return_low = 0
        self.capital_minus_fees_high = 0
        self.capital_minus_fees_low = 0
        self.return_final_high = 0
        self.return_final_low = 0
        self.tax_credit_high = 0
        self.tax_credit_low = 0
        self.taxes_high = 0
        self.taxes_low = 0
    
    def add_unused_high(self, high):
        self.unused_high = round(high,2)

    def add_unused_low(self,low):
        self.unused_low = round(low,2)

    def add_stock_amounts(self, high, low):
        self.stock_amount_high = high
        self.stock_amount_low = low

    def add_returns(self, high, low):
        self.return_high = round(high,2)
        self.return_low = round(low,2)

    def add_capital_minus_fees(self, high, low):
        self.capital_minus_fees_high = round(high,2)
        self.capital_minus_fees_low = round(low,2)
    
    def add_return_minus_fees(self, high, low):
        self.return_final_high = round(high,2)
        self.return_final_low = round(low,2)

    def add_taxes_high(self, high):
        self.taxes_high = round(high,2)

    def add_taxes_low(self,low):
        self.taxes_low = round(low,2)

    def add_tax_credit_high(self, high):
        self.tax_credit_high = round(high,2)

    def add_tax_credit_low(self, low):
        self.tax_credit_low = round(low,2)


class Package:
    def __init__(self):
        self.ticker = []
        self.firms = []
        self.ids = []
        self.highs = []
        self.mediums = []
        self.lows = []
        self.average_high = 0
        self.average_medium = 0
        self.average_low = 0
        self.trades = []

    def add_values(self, trade_data, ticker):
        self.highs.append(trade_data[3])
        self.mediums.append(trade_data[4])
        self.lows.append(trade_data[5])

    def add_company_id(self, firm_id):
        self.ids.append(firm_id)

    def calc_average(self):
        self.average_high = round(sum(self.highs)/len(self.highs), 2)
        self.average_low = round(sum(self.lows)/len(self.lows), 2)
        self.average_medium = round(self.average_high+self.average_low / 2, 2)

    def add_trade(self, trade_data, ticker, name):
        # 0 buy_date, 1 sell_date, 2 ticker, 3 buy_high, 4 buy_low , 5 sell_high , 6 sell_low, 7 name, 8 div%, 9 dividend, 10, dayline200
        self.trades.append([trade_data[9], trade_data[10], ticker,
                            trade_data[11], trade_data[12], trade_data[13], trade_data[14], name, trade_data[6],trade_data[7],trade_data[8]])


def test_against_indizes(packages, timeframe):
    # print("inzides")
    SP500 = 195.6836266310714
    DAX = 149.3108020832396
    SP500_threshold = SP500*1.05  # 1.05
    DAX_threshold = DAX*1.05  # 1.05
    accepted_packages = []
    for key in packages.keys():
        if packages[key].average_medium > SP500_threshold and packages[key].average_medium > DAX_threshold:
            accepted_packages.append(packages[key])
        else:
            print(key)

    return accepted_packages


def backtesting(package, timeframe, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low):
    last_dates = []
    fees = 0.01  #0.01
    taxes = 0.275 #0.275
    high_hist = []
    medium_hist = []
    low_hist = []
    backtest_breackdowns = {}
    for trade in package.trades:
        backtest_breackdowns[trade[0]] = Backtest_Breakdown(trade[0], trade[1], trade[7], trade[2], timeframe, amount_high, amount_low, trade[3], trade[4], trade[5], trade[6], trade[8], trade[9], trade[10])
        fees_amount_high = math.ceil(amount_high*fees)
        fees_amount_low = math.ceil(amount_low*fees)
        amount_high -= round(fees_amount_high,2)
        amount_low -= round(fees_amount_low,2)
        backtest_breackdowns[trade[0]].add_capital_minus_fees(amount_high, amount_low)
        stocks_high = int(amount_high/trade[4])
        stocks_low = int(amount_low/trade[3])

        if stocks_high == 0:
            if amount_high*1.1 < trade[4]:
                amount_high += fees_amount_high
                unused_high = 0
            if amount_high*1.1 >= trade[4]:
                stocks_high = 1
                amount_high = round(stocks_high*(trade[5]+trade[9]), 2)
                unused_high = 0
        else:
            unused_high = round(amount_high - (stocks_high*trade[4]),2)
            backtest_breackdowns[trade[0]].add_unused_high(unused_high)
            amount_high = round(stocks_high*(trade[5]+trade[9]), 2)
        if amount_high == 0.0:
            print("amount_low = 0.0", stocks_high, trade[6], trade[9])

        if stocks_low == 0:
            if amount_low*1.1 < trade[3]:
                amount_low += fees_amount_low
                unused_low = 0
            if amount_low*1.1 >= trade[3]:
                stocks_low = 1
                amount_low = round(stocks_low*(trade[6]+trade[9]), 2)
                unused_low = 0
        else:
            unused_low = round(amount_low - (stocks_low*trade[3]),2)
            backtest_breackdowns[trade[0]].add_unused_low(unused_low)
            amount_low = round(stocks_low*(trade[6]+trade[9]), 2)
        if amount_low == 0.0:
            print("amount_low = 0.0", stocks_low, trade[6], trade[3])
        
        amount_high -= round(amount_high*fees,2)
        amount_low -= round(amount_low*fees,2)
        backtest_breackdowns[trade[0]].add_returns(amount_high, amount_low)

        if amount_high < backtest_breackdowns[trade[0]].capital_minus_fees_high:
            tax_credit_high += round(((backtest_breackdowns[trade[0]].capital_minus_fees_high+fees_amount_high) - amount_high)*taxes,2)
            backtest_breackdowns[trade[0]].add_tax_credit_high(tax_credit_high)
            amount_high += unused_high
        else:
            backtest_breackdowns[trade[0]].add_tax_credit_high(tax_credit_high)
            taxes_high = round((amount_high - (backtest_breackdowns[trade[0]].capital_minus_fees_high+fees_amount_high))*taxes,2)
            if taxes_high < 0:
                taxes_high = 0  
            backtest_breackdowns[trade[0]].add_taxes_high(taxes_high)
            taxes_high2 = taxes_high
            taxes_high -= tax_credit_high
            tax_credit_high = round(tax_credit_high-taxes_high2,2)
            if tax_credit_high < 0:
                tax_credit_high = 0
            if taxes_high < 0:
                taxes_high = 0       
            amount_high -= taxes_high
            amount_high += unused_high

        if amount_low < backtest_breackdowns[trade[0]].capital_minus_fees_low:
            tax_credit_low += round(((backtest_breackdowns[trade[0]].capital_minus_fees_low+fees_amount_low) - amount_low)*taxes,2)
            backtest_breackdowns[trade[0]].add_tax_credit_low(tax_credit_low)
            amount_low += unused_low
        else:
            backtest_breackdowns[trade[0]].add_tax_credit_low(tax_credit_low)
            taxes_low =  round((amount_low - (backtest_breackdowns[trade[0]].capital_minus_fees_low+fees_amount_low))*taxes,2)
            if taxes_low < 0:
                taxes_low = 0  
            backtest_breackdowns[trade[0]].add_taxes_low(taxes_low)
            taxes_low2 = taxes_low
            taxes_low -= tax_credit_low
            tax_credit_low = round(tax_credit_low-taxes_low2,2)
            if tax_credit_low < 0:
                tax_credit_low = 0
            if taxes_low < 0:
                taxes_low = 0  
            amount_low -= taxes_low
            amount_low += unused_low
        backtest_breackdowns[trade[0]].add_stock_amounts(stocks_high, stocks_low)
        backtest_breackdowns[trade[0]].add_return_minus_fees(amount_high, amount_low)

        amount_medium = round((amount_high+amount_low)/2,2)
        high_hist.append(round(amount_high,2))
        medium_hist.append(round(amount_medium,2))
        low_hist.append(round(amount_low,2))
        last_dates.append(package.trades[-1][1])

    final_amount_high = round(amount_high, 2)
    final_amount_medium = round(amount_medium, 2)
    final_amount_low = round(amount_low, 2)
    last_date = last_dates[0]

    return final_amount_high, final_amount_medium, final_amount_low, last_date, high_hist, medium_hist, low_hist, backtest_breackdowns, tax_credit_high,tax_credit_low


def get_packages(package, timeframe, year, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low):
    print(year)
    db_connection = sqlite3.connect('./databases/div_trade_v8b.db') #7
    db_cursor = db_connection.cursor()
    package_object = Package()
    package = package[1]
    for n in range(len(package)):
        company_id = str(package[n][3])
        index = company_id.find(".")
        db_id = company_id[:index]
        counter = int(company_id[index+1:])-1
        if company_id not in package_object.ids:
            package_object.add_company_id(company_id)
            db_cursor.execute(
                f"SELECT * FROM '{year}' WHERE Timeframe = '{timeframe}' AND Company_ID = {db_id}")
            trade_data = db_cursor.fetchall()
            db_cursor.execute(f"SELECT Ticker FROM Companies WHERE ID = {db_id}")
            ticker = db_cursor.fetchone()
            ticker = ticker[0]
            db_cursor.execute(f"SELECT Company FROM Companies WHERE ID = {db_id}")
            name = db_cursor.fetchone()
            name = name[0]
            if counter >= len(trade_data):
                counter = len(trade_data)-1
            try:
                trade_data = trade_data[counter]
            except IndexError:
                print("! INDEXERROR", trade_data, counter, company_id, db_id)
            package_object.add_trade(trade_data, ticker, name)

    amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, backtest_breackdowns, tax_credit_high,tax_credit_low = backtesting(
        package_object, timeframe, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low)
    db_connection.close()
    return amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low
