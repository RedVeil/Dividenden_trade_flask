import backtest
import sqlite3
from datetime import date

def package_loop(ranking, counter, last_date=None ):
    # 0 start_date, 1 end_date, 2 points, 3 id, 4 name
    if last_date != None:
        for x in range(len(ranking)):
            if x >= counter:
                if ranking[x][0] >= last_date:
                    package = [ranking[x]]
                    break
        points = package[0][2]
        for i in ranking:
            if i[0] < package[-1][1] and i[0] >= package[-1][0] or i[1] > package[-1][0] and i[1] <= package[-1][1]:
                pass
            else:
                if i[0] >= package[-1][1]:
                    package.append(i)
                    points +=i[2]
                if i[1] <= package[0][0] and i[0] >= last_date:
                    package.insert(0,i)
                    points +=i[2]
    else:
        package = [ranking[counter]]
        points = package[0][2]
        for i in ranking:
            if i[0] < package[-1][1] and i[0] >= package[-1][0] or i[1] > package[-1][0] and i[1] <= package[-1][1]:
                pass
            else:
                if i[0] >= package[-1][1]:
                    package.append(i)
                    points +=i[2]
                if i[1] <= package[0][0]:
                    package.insert(0,i)
                    points +=i[2]
    return package, points

def package_loop_datetime(ranking, counter, last_date=None):
    # 0 start_date, 1 end_date, 2 points, 3 id, 4 name
    if last_date != None:
        last_date = date(int(last_date[:4]),int(last_date[5:7]),int(last_date[-2:]))
        for x in range(len(ranking)):
            if x >= counter:
                if ranking[x][0] >= last_date:
                    package = [ranking[x]]
                    break
        points = package[0][2]
        for i in ranking:
            if i[0] < package[-1][1] and i[0] >= package[-1][0] or i[1] > package[-1][0] and i[1] <= package[-1][1]:
                pass
            else:
                if i[0] >= package[-1][1]:
                    package.append(i)
                    points +=i[2]
                if i[1] <= package[0][0] and i[0] >= last_date:
                    package.insert(0,i)
                    points +=i[2]
    else:
        package = [ranking[counter]]
        points = package[0][2]
        for i in ranking:
            if i[0] < package[-1][1] and i[0] >= package[-1][0] or i[1] > package[-1][0] and i[1] <= package[-1][1]:
                pass
            else:
                if i[0] >= package[-1][1]:
                    package.append(i)
                    points +=i[2]
                if i[1] <= package[0][0]:
                    package.insert(0,i)
                    points +=i[2]
    return package, points

def sort_ranking(ranking, timeframe, last_date):
    ranking.sort()
    packages = {}
    counter = 0
    while counter < 10: #10 or more (amount of packages)
        if type(ranking[0][0]) != str:
            package, points = package_loop_datetime(ranking, counter, last_date)
        else:
            package, points = package_loop(ranking, counter, last_date)
        packages[counter] = [points, package]
        counter += 1
    to_sort = []
    for key in packages.keys():
        to_sort.append((packages[key][0], key))
    to_sort.sort()
    to_sort.reverse()
    best_package = packages[packages.keys() == to_sort[0]]
    return best_package


def get_firms_from_db(raw_data, raw_data2,timeframe, year, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low, last_date=None):
    ranking = []
    for row in raw_data:
        for row2 in raw_data2:
            if row[2] in row2:
                if row[6] != "American-Funds-Int-Bond-Fd-of-A":
                    ranking.append([row2[4], row2[5], row[3], row[2], row[6]])
    package = sort_ranking(ranking, timeframe, last_date)
    amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low = backtest.get_packages(package,timeframe, year, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low)
    return amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low

def expert_get_firms_from_db(companies_last_year, companies,timeframe, year, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low, last_date=None):
    ranking = []
    for key in companies_last_year.keys():
        if key in companies.keys():
            if companies_last_year[key].name != "American-Funds-Int-Bond-Fd-of-A":
                ranking.append([companies[key].start_date, companies[key].end_date, companies_last_year[key].points, companies_last_year[key].id, companies_last_year[key].name])
    package = sort_ranking(ranking, timeframe, last_date)
    amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low = backtest.get_packages(package,timeframe, year, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low)
    return amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low



def web_call(timeframe_buy, timeframe_sell, start_year, end_year):
    total_years = [2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018]
    years = total_years[total_years.index(int(start_year)):total_years.index(int(end_year))+1]
    db_connection = sqlite3.connect('./databases/indicator_db_v3.db') #_v2
    db_cursor = db_connection.cursor() 
    high_hists = {}
    medium_hists = {}
    low_hists = {}
    package_objects = {}
    breakdowns_per_year = {}
    timeframe = f"{timeframe_buy}-{timeframe_sell}"
    amount_highs=[1000]
    amount_mediums=[1000]
    amount_lows=[1000]
    tax_credit_high = 0
    tax_credit_low = 0
    for year in years:
        db_cursor.execute(f"SELECT * FROM '{year-1}' WHERE Timeframe = '{timeframe}'")
        raw_data = db_cursor.fetchall()
        db_cursor.execute(f"SELECT * FROM '{year}' WHERE Timeframe = '{timeframe}'")
        raw_data2 = db_cursor.fetchall()
        if year == years[0]:
            amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low = get_firms_from_db(raw_data, raw_data2, timeframe, year, amount_highs[-1], amount_mediums[-1], amount_lows[-1], tax_credit_high, tax_credit_low)
        else:
            amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high,tax_credit_low = get_firms_from_db(raw_data, raw_data2, timeframe, year, amount_highs[-1], amount_mediums[-1], amount_lows[-1], tax_credit_high, tax_credit_low, last_date)
        high_hists[year] = high_hist
        medium_hists[year] = medium_hist
        low_hists[year] = low_hist
        package_objects[year] = package_object
        breakdowns_per_year[year] = backtest_breackdowns
        amount_highs.append(amount_high)
        amount_mediums.append(amount_medium)
        amount_lows.append(amount_low)

    db_connection.close()
    return high_hists, medium_hists, low_hists, package_objects, breakdowns_per_year

