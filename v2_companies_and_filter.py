import sqlite3
import locale
import v2_packages as packages
import v2_backtest as backtest
from datetime import date, timedelta

locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

class Trade:
    def __init__(self, buy_date, sell_date, buy_high, buy_low, buy_close, sell_high,sell_low, sell_close, buy_volume, sell_volume):
        self.buy_date = buy_date
        self.sell_date = sell_date
        self.buy_high= round(buy_high,2)
        self.buy_low= round(buy_low,2)
        self.buy_close = round(buy_close,2)
        self.sell_high= round(sell_high,2)
        self.sell_low= round(sell_low,2)
        self.sell_close = round(sell_close,2)
        self.buy_volume = buy_volume
        self.sell_volume = sell_volume
        self.high_return = {}
        self.low_return = {}
        self.close_return = {}
        self.average_return = {}

    def calc_returns(self, buy_price, sell_price, dividend_amount):
        return_amount = sell_price + dividend_amount - buy_price
        return_percent = round((return_amount/buy_price)*100,2)
        return_amount = round(return_amount,2)
        return return_amount, return_percent

    def add_returns(self, dividend_amount):
        high_amount, high_percent = self.calc_returns(self.buy_low, self.sell_high, dividend_amount)
        low_amount, low_percent = self.calc_returns(self.buy_high, self.sell_low, dividend_amount)
        close_amount, close_percent = self.calc_returns(self.buy_close, self.sell_close, dividend_amount)
        self.high_return = {"amount":high_amount,"percent":high_percent}
        self.low_return = {"amount":low_amount,"percent":low_percent}
        self.close_return = {"amount":close_amount,"percent":close_percent}
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
        if buy_values == [] or sell_values == []:
            x = [1,-1,2,-2,3,-3,4,-4,5,-5,6,-6,7,-7,8,-8,9,-9,10,-10,11,-11,12,-12,13,-13,14,-14]
            for i in x:
                datetime_date = date(int(dividend_date[:4]), int(dividend_date[5:7]), int(dividend_date[-2:]))
                new_dividend_date = datetime_date - timedelta(days=i)
                str_dividend_date = new_dividend_date.strftime("%Y-%m-%d")
                buy_values, sell_values = self.get_buy_sell_values(ticker, str_dividend_date, db_connection, db_cursor, timeframe_buy, timeframe_sell)
                if buy_values != [] and sell_values != []:
                    self.trades[year]=Trade(buy_values[0][1],sell_values[0][1],buy_values[0][2],buy_values[0][3],
                                        buy_values[0][4],sell_values[0][2],sell_values[0][3],sell_values[0][4],buy_values[0][5],sell_values[0][5])
                    self.trades[year].add_returns(dividend_amount)
                    self.add_trend200(year, ticker, buy_values[0][0], buy_values[0][4], db_connection, db_cursor)
                    return True
                if buy_values == [] and i == x[-1]:
                    return False
                    
        else:
            self.trades[year]=Trade(buy_values[0][1],sell_values[0][1],buy_values[0][2],buy_values[0][3],
                                    buy_values[0][4],sell_values[0][2],sell_values[0][3],sell_values[0][4],buy_values[0][5],sell_values[0][5])
            self.trades[year].add_returns(dividend_amount)
            self.add_trend200(year, ticker, buy_values[0][0], buy_values[0][4], db_connection, db_cursor)
            return True

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

    def calc_strikes(self, year, form_data):
        strikes = 0
        if self.average_returns[year] < int(form_data["average_threshold"]):
            strikes += int(form_data["average_strikes"])
        if self.median_returns[year] < int(form_data["median_threshold"]):
            strikes += int(form_data["median_strikes"])
        if self.bad_trades[year] > int(form_data["bad_trades_threshold"]):
            strikes += int(form_data["bad_trades_strikes"])
        if self.bad_trades[year] > int(form_data["bad_trades2_threshold"]):
            strikes += int(form_data["bad_trades2_strikes"])
        if self.severe_trades[year] > int(form_data["severe_trades_threshold"]):
            strikes += int(form_data["severe_trades_strikes"])
        if self.great_trades[year] < int(form_data["great_trades_threshold"]):
            strikes += int(form_data["great_trades_strikes"])
        self.strikes[year] = strikes

    def add_ranking_points(self, year, points):
        self.ranking_points[year] = points

class Companies:
    def __init__(self):
        self.companies = {}
    
    def add_company(self, ID, company):
        self.companies[ID] = company

    def fill_companies(self,year, years, db_connection, db_cursor, company_infos, dividends_data, timeframe_buy, timeframe_sell, form_data):
        trades = 0
        for row in dividends_data:
            if row[1] < 10000:
                ticker = company_infos[row[1]]["ticker"]
                ID = f"{ticker}-{row[2]}"
                if ID in self.companies.keys():   
                    if self.companies[ID].add_trade(year, company_infos[row[1]]["ticker"], row[3],row[4], db_connection, db_cursor, timeframe_buy, timeframe_sell):
                        self.companies[ID].add_dividend_values(year, row[3],row[4],row[5])
                        self.companies[ID].calc_average(year)
                        self.companies[ID].calc_median(year)
                        self.companies[ID].assess_trades(year)
                        self.companies[ID].calc_strikes(year, form_data)
                        trades += 1
                else:
                    new_company = Company(company_infos[row[1]]["ticker"],company_infos[row[1]]["name"],row[1])
                    self.add_company(ID, new_company)
                    if self.companies[ID].add_trade(year, company_infos[row[1]]["ticker"], row[3],row[4], db_connection, db_cursor, timeframe_buy, timeframe_sell):
                        self.companies[ID].add_dividend_values(year, row[3],row[4],row[5])
                        self.companies[ID].calc_average(year)
                        self.companies[ID].calc_median(year)
                        self.companies[ID].assess_trades(year)
                        self.companies[ID].calc_strikes(year, form_data)
                        trades += 1
        return trades

    def calc_indicator(self, year, companies, form_data):
        averages_rank = []
        medians_rank = []
        bad_trades_rank = []
        severe_trades_rank = []
        great_trades_rank = []
        for key in companies.keys():
            averages_rank.append((self.companies[key].average_returns[year], key))
            medians_rank.append((self.companies[key].median_returns[year], key))
            bad_trades_rank.append((self.companies[key].bad_trades[year], key))
            severe_trades_rank.append((self.companies[key].severe_trades[year], key))
            great_trades_rank.append((self.companies[key].great_trades[year], key))

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
                    points += n * (int(form_data["averages_multiplier"])/100)
                if key in medians_rank[n]:
                    points += n * (int(form_data["medians_multiplier"])/100)
                if key in bad_trades_rank[n]:
                    points += n * (int(form_data["bad_trades_multiplier"])/100)
                if key in severe_trades_rank[n]:
                    points += n * (int(form_data["severe_trades_multiplier"])/100)
                if key in great_trades_rank[n]:
                    points += n * (int(form_data["great_trades_multiplier"])/100)
            self.companies[key].add_ranking_points(year, points)

def add_decimals(formated_number):
    try:
        decimals = formated_number[formated_number.index(",")+1:]
        if(len(decimals)<2):
            new_formated = formated_number+"0"
            return new_formated
        else:
            return formated_number
    except ValueError:
        new_formated = formated_number+",00"
        return new_formated

def format_backtest(breakdowns):
    for breakdown in breakdowns:
        breakdown.working_capital_high = add_decimals('{0:n}'.format(breakdown.working_capital_high))
        breakdown.working_capital_low = add_decimals('{0:n}'.format(breakdown.working_capital_low))
        breakdown.working_capital_close = add_decimals('{0:n}'.format(breakdown.working_capital_close))

        breakdown.invest_high = add_decimals('{0:n}'.format(breakdown.invest_high))
        breakdown.invest_low = add_decimals('{0:n}'.format(breakdown.invest_low))
        breakdown.invest_close = add_decimals('{0:n}'.format(breakdown.invest_close))

        breakdown.high_fees = add_decimals('{0:n}'.format(breakdown.high_fees))
        breakdown.low_fees = add_decimals('{0:n}'.format(breakdown.low_fees))
        breakdown.close_fees = add_decimals('{0:n}'.format(breakdown.close_fees))

        breakdown.unused_high = add_decimals('{0:n}'.format(breakdown.unused_high))
        breakdown.unused_low = add_decimals('{0:n}'.format(breakdown.unused_low))
        breakdown.unused_close = add_decimals('{0:n}'.format(breakdown.unused_close))

        breakdown.buy_high = add_decimals('{0:n}'.format(breakdown.buy_high))
        breakdown.buy_low = add_decimals('{0:n}'.format(breakdown.buy_low))
        breakdown.buy_close = add_decimals('{0:n}'.format(breakdown.buy_close))

        breakdown.sell_high = add_decimals('{0:n}'.format(breakdown.sell_high))
        breakdown.sell_low = add_decimals('{0:n}'.format(breakdown.sell_low))
        breakdown.sell_close = add_decimals('{0:n}'.format(breakdown.sell_close))

        breakdown.dividend = add_decimals('{0:n}'.format(breakdown.dividend))

        breakdown.return_high = add_decimals('{0:n}'.format(breakdown.return_high))
        breakdown.return_low = add_decimals('{0:n}'.format(breakdown.return_low))
        breakdown.return_close = add_decimals('{0:n}'.format(breakdown.return_close))

        breakdown.return_minus_fees_high = add_decimals('{0:n}'.format(breakdown.return_minus_fees_high))
        breakdown.return_minus_fees_low = add_decimals('{0:n}'.format(breakdown.return_minus_fees_low))
        breakdown.return_minus_fees_close = add_decimals('{0:n}'.format(breakdown.return_minus_fees_close))
        
        breakdown.return_pre_tax_high = add_decimals('{0:n}'.format(breakdown.return_pre_tax_high))
        breakdown.return_pre_tax_low = add_decimals('{0:n}'.format(breakdown.return_pre_tax_low))
        breakdown.return_pre_tax_close = add_decimals('{0:n}'.format(breakdown.return_pre_tax_close))

        breakdown.tax_credit_high = add_decimals('{0:n}'.format(breakdown.tax_credit_high))
        breakdown.tax_credit_low = add_decimals('{0:n}'.format(breakdown.tax_credit_low))
        breakdown.tax_credit_close = add_decimals('{0:n}'.format(breakdown.tax_credit_close))

        breakdown.taxes_high = add_decimals('{0:n}'.format(breakdown.taxes_high))
        breakdown.taxes_low = add_decimals('{0:n}'.format(breakdown.taxes_low))
        breakdown.taxes_close = add_decimals('{0:n}'.format(breakdown.taxes_close))

        breakdown.return_minus_taxes_high = add_decimals('{0:n}'.format(breakdown.return_minus_taxes_high))
        breakdown.return_minus_taxes_low = add_decimals('{0:n}'.format(breakdown.return_minus_taxes_low))
        breakdown.return_minus_taxes_close = add_decimals('{0:n}'.format(breakdown.return_minus_taxes_close))

        breakdown.return_final_high = add_decimals('{0:n}'.format(breakdown.return_final_high))
        breakdown.return_final_low = add_decimals('{0:n}'.format(breakdown.return_final_low))
        breakdown.return_final_close = add_decimals('{0:n}'.format(breakdown.return_final_close))

    return breakdowns



def filter_company(year, years, company, key, volume_threshold, daily_increase_threshold, total_increase_threshold, error_counter):
    #print(key)
    if year == years[0]:
        if year not in company.trades.keys():
            #print("year not in trades")
            error_counter["No_Trade_Key"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if year not in company.average_returns.keys():
            error_counter["No_Trade_Key"] += 1
            error_counter["Total"] += 1
            return None 
        elif company.trades[year].buy_date == None:
            error_counter["No_Buy_Date"] += 1
            error_counter["Total"] += 1
            #print("No buy date")
            return 0, error_counter
        elif company.dividends[year]["percent"] > 10:
            error_counter["High_Dividend"] +=1
            error_counter["Total"] += 1
            #print("dividend to high")
            return 0, error_counter
        elif company.bad_trades[year] > 50: #50
            #print(f"bad Trades: {company.bad_trades}")
            error_counter["Bad_Trades"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        elif company.severe_trades[year] > 10: #10
            #print(f"severe Trades: {company.severe_trades}")
            error_counter["Severe_Trades"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        elif company.average_returns[year] < 1:
            error_counter["Avg_Returns"] += 1
            error_counter["Total"] += 1
            #print(f"average return: {company.average_returns[year]}")
            return 0, error_counter
        elif company.median_returns[year] < 0:
            error_counter["Median_Returns"] += 1
            error_counter["Total"] += 1
            #print(f"median return: {company.median_returns[year]}")
            return 0, error_counter
        elif company.trades[year].buy_volume < volume_threshold or company.trades[year].sell_volume < volume_threshold:
            #print("Volume to low")
            return 0, error_counter
        elif company.trades[year].buy_close*daily_increase_threshold < company.trades[year].sell_close:
            #print("daily increase threshold")
            return 0, error_counter
        elif company.trades[year].buy_close*total_increase_threshold < company.trades[year].sell_close:
            #print("total increase threshold")
            return 0, error_counter
        else:
            error_counter["Nothing"] += 1
            error_counter["Total"] += 1
            return 1, error_counter
    else:
        try:
            blub = company.strikes[year-1]
        except KeyError:
            #print(f"{key} - KeyError")
            #print(company.strikes)
            error_counter["KeyError"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if company.strikes[year-1] >= 10: #10
            #print(f"{company.strikes[year]} Strikes")
            error_counter["Strikes"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if year-1 not in company.trades.keys():
            #print("year and previous year not in trade keys")
            #print(company.trades.keys())
            error_counter["Last_Year_Trades"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        """if year-1 not in company.ranking_points.keys():
            #print("year and previous year not in ranking keys")
            #print(company.ranking_points.keys())
            error_counter["Last_Year_Ranking"] += 1
            error_counter["Total"] += 1
            return 0, error_counter"""
        if year not in company.trades.keys():
            #print("year not in trades")
            error_counter["No_Trade_Key"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if year not in company.average_returns.keys():
            error_counter["No_Trade_Key"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if company.trades[year].buy_date == None:
            error_counter["No_Buy_Date"] += 1
            error_counter["Total"] += 1
            #print("No buy date")
            return 0, error_counter
        if company.dividends[year]["percent"] > 10:
            error_counter["High_Dividend"] +=1
            error_counter["Total"] += 1
            #print("dividend to high")
            return 0, error_counter
        if company.bad_trades[year] > 50: #50
            #print(f"bad Trades: {company.bad_trades}")
            error_counter["Bad_Trades"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if company.severe_trades[year] > 10: #10
            #print(f"severe Trades: {company.severe_trades}")
            error_counter["Severe_Trades"] += 1
            error_counter["Total"] += 1
            return 0, error_counter
        if company.average_returns[year] < 1:
            error_counter["Avg_Returns"] += 1
            error_counter["Total"] += 1
            #print(f"average return: {company.average_returns[year]}")
            return 0, error_counter
        if company.median_returns[year] < 0:
            error_counter["Median_Returns"] += 1
            error_counter["Total"] += 1
            #print(f"median return: {company.median_returns[year]}")
            return 0, error_counter
        if company.trades[year].buy_volume < volume_threshold or company.trades[year].sell_volume < volume_threshold:
            #print("Volume to low")
            return 0, error_counter
        if company.trades[year].buy_close*daily_increase_threshold < company.trades[year].sell_close:
            #print("daily increase threshold")
            return 0, error_counter
        if company.trades[year].buy_close*total_increase_threshold < company.trades[year].sell_close:
            #print("total increase threshold")
            return 0, error_counter
        else:
            error_counter["Nothing"] += 1
            error_counter["Total"] += 1
            return 1, error_counter

def filter_loop(year, years, companies, volume_threshold, daily_increase_threshold, total_increase_threshold):
    filtered_companies = {}
    error_counter={"Total":0,"Strikes":0,"KeyError":0,"No_Trade_Key":0,"High_Dividend":0,"Bad_Trades":0,"Severe_Trades":0,"Avg_Returns":0,"Median_Returns":0,"No_Buy_Date":0,"Last_Year_Trades":0,"Last_Year_Ranking":0,"Nothing":0}
    for key in companies.keys():
        status, error_counter = filter_company(year, years, companies[key], key, volume_threshold, daily_increase_threshold, total_increase_threshold, error_counter)
        if status == 1:
            filtered_companies[key] = companies[key]
    return filtered_companies,error_counter


def webcall(form_data):
    total_years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008,
                   2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    end_year = int(form_data["trade_years"][form_data["trade_years"].index(";")+1:])
    start_year = int(form_data["trade_years"][:form_data["trade_years"].index(";")])
    years = total_years[total_years.index(int(start_year))-1:total_years.index(int(end_year))+1]
    timeframe_buy = int(form_data["timeframe"][:form_data["timeframe"].index(";")])*-1
    timeframe_sell = int(form_data["timeframe"][form_data["timeframe"].index(";")+1:])
    timeframe = f"{timeframe_buy}-{timeframe_sell}"
    print(timeframe)
    db_connection = sqlite3.connect('./databases/div_trade_v9c.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT * FROM '01_Companies'")
    db_company_infos = db_cursor.fetchall()
    company_infos = {}
    for row in db_company_infos:
        if row[3] != "US":
            company_infos[row[0]] = {"name":row[1],"currency":row[3],"ticker":row[2]}
    all_companies = Companies()
    
    last_date = ""
    safety_margin = 1 #(100-float(form_data["safety_margin"]))/100
    volume_threshold = 0#int(form_data["volume_threshold"])
    daily_increase_threshold =  1.15#(1+(int(form_data["daily_increase_threshold"])/100))**(timeframe_buy+timeframe_sell)
    total_increase_threshold =  1.15#int(form_data["daily_increase_threshold"])+100
    amount_high = int(form_data["start_amount"])
    amount_low = int(form_data["start_amount"])
    amount_close = int(form_data["start_amount"])
    tax_credit_high = 0
    tax_credit_low = 0
    tax_credit_close = 0
    backtest_breackdowns = {}
    global_error_counter = {}
    total_trade_counter = {}
    
    for year in years:
        print(year)
        db_cursor.execute(f"SELECT * FROM 'dividends_{year}'")
        dividends_data = db_cursor.fetchall()
        trade_counter = all_companies.fill_companies(year, years, db_connection, db_cursor, company_infos, dividends_data, timeframe_buy, timeframe_sell, form_data) 
        total_trade_counter[year] = trade_counter
        print("total_trades")
        print(total_trade_counter)
        filtered_companies, error_counter = filter_loop(year, years, all_companies.companies, volume_threshold, daily_increase_threshold, total_increase_threshold)     
        global_error_counter[year] = error_counter
        print("calc_indicator") 
        print(len(filtered_companies))      
        all_companies.calc_indicator(year, filtered_companies, form_data)
        if year == years[1]:
            print("create first package")
            best_package = packages.get_companies(filtered_companies, year)
            print("create first backtest")
            last_date, amount_high, amount_low, amount_close, tax_credit_high, tax_credit_low, tax_credit_close, backtest_breackdown = backtest.backtesting(timeframe, best_package, amount_high, amount_low, amount_close, tax_credit_high, tax_credit_low, tax_credit_close, safety_margin)
            formated_breackdown = format_backtest(backtest_breackdown)
            backtest_breackdowns[year] =  formated_breackdown
        if year > years[1]:
            print("create package")
            best_package = packages.get_companies(filtered_companies, year, last_date)
            print("create backtest")
            last_date, amount_high, amount_low, amount_close, tax_credit_high, tax_credit_low, tax_credit_close, backtest_breackdown = backtest.backtesting(
                    timeframe, best_package, amount_high, amount_low, amount_close,tax_credit_high, tax_credit_low, tax_credit_close,safety_margin)
            formated_breackdown = format_backtest(backtest_breackdown)
            backtest_breackdowns[year] = formated_breackdown
        
    print(global_error_counter)
    
    
    return backtest_breackdowns
