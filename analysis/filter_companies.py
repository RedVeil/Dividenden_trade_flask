import sqlite3
from datetime import date
import create_indicator as indicator

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
        
    # 6
    def add_high2018(self, high_2018):
        self.high_2018 = high_2018


    def calc_average(self):
        self.average_high = round(sum(self.highs.values())/len(self.highs.values()),2)
        self.average_medium = round(sum(self.mediums.values())/len(self.mediums.values()),2)
        self.average_low = round(sum(self.lows.values())/len(self.lows.values()),2)

    # 7
    def calc_median(self):
        high = sorted(self.highs.values())
        medium = sorted(self.mediums.values())
        low = sorted(self.lows.values())
        minus = sorted(self.minus_trades.values())
        self.median_high = round(high[int(len(self.highs.values())/2)],2)
        self.median_medium = round(medium[int(len(self.mediums.values())/2)],2)
        self.median_low = round(low[int(len(self.lows.values())/2)],2)
        try:
            self.median_minus = round(minus[int(len(self.minus_trades.values())/2)],2)
        except IndexError:
            self.median_minus = 0

    def count_trades(self):
        for trade in self.mediums.values():
            if trade < 0:
                self.bad_trades += 1
                self.minus_trades.append(trade)
            if trade < -5:
                self.severe_trades += 1
            if trade > 10:
                self.great_trades += 1
        self.bad_trades = round(self.bad_trades / len(self.mediums.values())*100,2)
        self.severe_trades = round(self.severe_trades / len(self.mediums.values())*100,2)
        self.great_trades = round(self.great_trades / len(self.mediums.values())*100,2)
        years_paid = len(self.dividends.keys())
        if years_paid < 1:
            years_paid = 1
        try:
            self.years_dividend_paid = round(years_paid/ self.firm_years*100,2)
        except ZeroDivisionError:
            print(years_paid, self.firm_years, self.name)

    def calc_strikes(self):
        if self.average_high < 10:
            self.strikes += 1
        if self.average_medium < 5:
            self.strikes += 1
        if self.average_low < 2:
            self.strikes += 1
        if self.median_high < 10:
            self.strikes += 1
        if self.median_medium < 5:
            self.strikes += 1
        if self.median_low < 1:
            self.strikes += 1
        if self.bad_trades > 10:
            self.strikes += 2
        if self.bad_trades > 20:
            self.strikes += 4 #4
        if self.severe_trades > 10:
            self.strikes += 4 #4
        if self.great_trades < 5:
            self.strikes += 1


def fetch_company(raw_data,companies, year):
    counter = 0
    try:
        start_id = str(raw_data[0][1])
    except IndexError:
        print(year, raw_data)
        
    for row in raw_data:
        if str(row[1]) == start_id:
            counter += 1
        if str(row[1]) != start_id:
            counter = 1
            start_id = str(row[1])
        firm_id = f"{row[1]}.{counter}"
        if firm_id not in companies.keys():
            db_connection = sqlite3.connect('C:\\Users\\Leon\\dividenden_trade\\backend\\analysis\\databases\\div_trade_v7.db')
            db_cursor = db_connection.cursor()   
            db_cursor.execute(f"SELECT Market FROM 'Companies' WHERE ID = '{row[1]}'")
            market = db_cursor.fetchone()
            if market[0] != "gb_market" or market[0] != "za_market":
                db_cursor.execute(f"SELECT Company FROM 'Companies' WHERE ID = '{row[1]}'")
                company_name = db_cursor.fetchone()
                db_cursor.execute(f"SELECT Ticker FROM 'Companies' WHERE ID = '{row[1]}'")
                ticker = db_cursor.fetchone()
                db_cursor.execute(f"SELECT Years FROM 'Companies' WHERE ID = '{row[1]}'")
                firm_years = db_cursor.fetchone()
                companies[firm_id] = Company(ticker[0], company_name[0], firm_id, firm_years[0])
                companies[firm_id].add_values(row, year)          
            db_cursor.close()
        else:
            companies[firm_id].add_values(row, year)
        if year == 2018:
            companies[firm_id].add_high2018(row[11])
        
        #print(companies[firm_id].start_dates[year], companies[firm_id].end_dates[year], companies[firm_id].name,companies[firm_id].id)
        
            
    return companies


def filter_firm(company):
    div_over50 = 0
    for i in company.dividends.values():
        if i > 50:
            div_over50 +=1
    if company.ticker == "RAM.LS":
        pass  
    else:
        if company.bad_trades > 50 or company.severe_trades > 10 or company.median_medium < 0 or company.firm_years < 12 or div_over50 > 2 or company.high_2018 < 10 or company.years_dividend_paid < 75:  #
            #print(company.bad_trades, company.severe_trades, company.median_medium, company.firm_years, "div_over50", div_over50, company.name, company.id, company.years_dividend_paid)
            pass
        else:
            #print("-", company.name, company.firm_years)
            company.calc_strikes()
            if company.strikes < 10:  
                '''print("_____________________________")      
                print(company.name)
                print(company.id)
                print(f"points: {company.strikes}")
                print(f"average high: {company.average_high}%")
                print(f"average medium: {company.average_medium}%")
                print(f"average low: {company.average_low}%")
                print(f"median high: {company.median_high}%")
                print(f"median average: {company.median_medium}%")
                print(f"median low: {company.median_low}%")
                print(f"bad trades: {company.bad_trades}%")
                print(f"severe trades: {company.severe_trades}%")
                print(f"great trades: {company.great_trades}%")         
                print()'''
                return company

# 2
def grab_data(year, companies, timeframe):
    db_connection = sqlite3.connect('C:\\Users\\Leon\\dividenden_trade\\backend\\analysis\\databases\\div_trade_v7.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT * FROM '{year}' WHERE Timeframe = '{timeframe}' ") # Dividends > 2 AND   #AND Company_ID = 637 AND Company_ID = 615
    raw_data = db_cursor.fetchall()
    companies = fetch_company(raw_data, companies, year)
    db_cursor.close()
    return companies



def webcall(form_data):
    total_years = [2019, 2018, 2017, 2016,2015, 2014, 2013,2012, 2011, 2010, 2009,2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001]
    years = total_years[total_years.index(form_data["start_year"]):total_years.index(form_data["end_year"])+1]
    companies = {}
    checked_firms = []
    medium_objects = []
    timeframe = f"{form_data["timeframe_buy"]}-{form_data["timeframe_sell"]}"
    print(timeframe)
    for year in years:
         companies = grab_data(year, companies, timeframe)
    for key in companies.keys():
        companies[key].calc_average()
        companies[key].count_trades()
        companies[key].calc_median()
        checked_firm = filter_firm(companies[key])
        if not checked_firm:
            pass
        else:
            checked_firms.append(checked_firm)

        indicator.web_get_accepted_companies(checked_firms, timeframe)
# 1
if __name__ == "__main__":
    years =  [2019, 2018, 2017, 2016,2015, 2014, 2013,2012, 2011, 2010, 2009,2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001] #,
    companies = {}
    checked_firms = []
    medium_objects = []
    timeframe_buy = 0 # Default 0
    while timeframe_buy < 60: #Default 60
        timeframe_buy += 1
        for i in range(11): # Default 11
            timeframe_sell = i #i
            timeframe = f"{timeframe_buy}-{timeframe_sell}"
            print(timeframe)
            for year in years:
                companies = grab_data(year, companies, timeframe)
            for key in companies.keys():
                companies[key].calc_average()
                companies[key].count_trades()
                companies[key].calc_median()
                checked_firm = filter_firm(companies[key])
                if not checked_firm:
                    pass
                else:
                    checked_firms.append(checked_firm)

            indicator.get_accepted_companies(checked_firms, timeframe)