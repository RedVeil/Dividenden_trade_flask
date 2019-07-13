import sqlite3
from datetime import date

class Companies:
    def __init__(self):
        self.companies = {}
    
    def add_company(self, ID, company):
        self.companies[ID] = company

class Company:
    def __init__(self, ticker, name, company_id, firm_years):
        self.ticker = ticker
        self.name = name
        self.id = company_id
        self.firm_years = firm_years
        self.highs = {}
        self.mediums = {}
        self.lows = {}
        self.dividends = {}
        self.day_lines200 = {}
        self.average_high = 0
        self.average_medium = 0
        self.average_low = 0
        self.median_high = 0
        self.median_medium = 0
        self.median_low = 0
        self.bad_trades = 0
        self.severe_trades = 0
        self.great_trades = 0
        self.start_dates = {}
        self.end_dates = {}
        self.strikes = 0
        self.minus_trades = []
        self.median_minus = 0
        self.high_2018 = 0
        self.years_dividend_paid = 0

    def add_values(self, row, year):
        self.highs[year] = row[3]
        self.mediums[year] = row[4]
        self.lows[year] = row[5]
        self.dividends[year] = row[6]
        self.day_lines200[year] = row[8]
        start_date = date(int(row[9][:4]), int(row[9][5:7]), int(row[9][-2:]))
        self.start_dates[year] = start_date
        end_date = date(int(row[10][:4]), int(row[10][5:7]), int(row[10][-2:]))
        self.end_dates[year] = end_date

    def add_high2018(self, high_2018):
        self.high_2018 = high_2018

    def calc_average(self):
        self.average_high = round(
            sum(self.highs.values())/len(self.highs.values()), 2)
        self.average_medium = round(
            sum(self.mediums.values())/len(self.mediums.values()), 2)
        self.average_low = round(
            sum(self.lows.values())/len(self.lows.values()), 2)

def grab_data(year, companies, timeframe):
    db_connection = sqlite3.connect('./databases/div_trade_v8b.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(
        f"SELECT * FROM '{year}' WHERE Timeframe = '{timeframe}' ")
    raw_data = db_cursor.fetchall()
    companies = fetch_company(raw_data, companies, year)
    db_cursor.close()
    return companies

def grab_dividends(year, db_connection, db_cursor):
    

def webcall(form_data):
    total_years = [2000,2001,2002, 2003, 2004, 2005, 2006, 2007, 2008,
                   2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    years = total_years[total_years.index(int(form_data["start_year"]))-1:total_years.index(int(form_data["end_year"]))]
    checked_firms = []
    timeframe_buy = form_data["timeframe_buy"]
    timeframe_sell = form_data["timeframe_sell"]
    timeframe = f"{timeframe_buy}-{timeframe_sell}"
    print(timeframe)
    db_connection = sqlite3.connect('./databases/div_trade_v8b.db')
    db_cursor = db_connection.cursor()
    for year in years:

        companies = grab_data(year, companies, timeframe)




    """for key in companies.keys():
        companies[key].calc_average()
        companies[key].count_trades()
        companies[key].calc_median()
        checked_firm = filter_firm(companies[key], form_data)
        if checked_firm:
            checked_firms.append(checked_firm)

    high_hists, medium_hists, low_hists, package_objects, breakdowns_per_year = indicator.get_accepted_companies(
        checked_firms, timeframe, form_data)
    return high_hists, medium_hists, low_hists, package_objects, breakdowns_per_year"""