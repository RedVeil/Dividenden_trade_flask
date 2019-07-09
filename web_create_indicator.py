import sqlite3
import web_build_packages as packages


class Company:
    def __init__(self, ticker, name, company_id, average_high, average_medium, average_low, median_high, median_medium, median_low, bad_trades, severe_trades, great_trades, start_date, end_date):
        self.ticker = ticker
        self.name = name
        self.id = company_id
        self.day_lines200 = {}
        self.average_high = average_high
        self.average_medium = average_medium
        self.average_low = average_high
        self.median_high = median_high
        self.median_medium = median_medium
        self.median_low = median_low
        self.bad_trades = 0
        self.severe_trades = 0
        self.great_trades = 0
        self.start_date = start_date
        self.end_date = end_date
        self.points = 0


def calc_indicator(companies, form_data):
    averages_rank = []
    medians_rank = []
    bad_trades_rank = []
    severe_trades_rank = []
    great_trades_rank = []
    for key in companies.keys():
        averages_rank.append((companies[key].average_medium, key))
        medians_rank.append((companies[key].median_medium, key))
        bad_trades_rank.append((companies[key].bad_trades, key))
        severe_trades_rank.append((companies[key].severe_trades, key))
        great_trades_rank.append((companies[key].great_trades, key))
    averages_rank.sort()
    medians_rank.sort()
    bad_trades_rank.sort()
    bad_trades_rank.reverse()
    severe_trades_rank.sort()
    bad_trades_rank.reverse()
    great_trades_rank.sort()
    for key in companies.keys():
        for n in range(len(averages_rank)):
            if key in averages_rank[n]:
                companies[key].points += n * \
                    (form_data["averages_multiplier"]/100)
            if key in medians_rank[n]:
                companies[key].points += n * \
                    (form_data["medians_multiplier"]/100)
            if key in bad_trades_rank[n]:
                companies[key].points += n * \
                    (form_data["bad_trades_multiplier"]/100)
            if key in severe_trades_rank[n]:
                companies[key].points += n * \
                    (form_data["severe_trades_multiplier"]/100)
            if key in great_trades_rank[n]:
                companies[key].points += n * \
                    (form_data["great_trades_multiplier"]/100)


def calc_average(temp_highs, temp_mediums, temp_lows):
    high_avg = round(sum(temp_highs)/len(temp_highs), 2)
    medium_avg = round(sum(temp_mediums)/len(temp_mediums), 2)
    low_avg = round(sum(temp_lows)/len(temp_lows), 2)
    return high_avg, medium_avg, low_avg


def calc_median(temp_highs, temp_mediums, temp_lows):
    high = sorted(temp_highs)
    medium = sorted(temp_mediums)
    low = sorted(temp_lows)
    median_high = round(high[int(len(temp_highs)/2)], 2)
    median_medium = round(medium[int(len(temp_mediums)/2)], 2)
    median_low = round(low[int(len(temp_lows)/2)], 2)
    return median_high, median_medium, median_low


def sort_trades(temp_mediums):
    bad_trades = 0
    severe_trades = 0
    great_trades = 0
    for trade in temp_mediums:
        if trade < 0:
            bad_trades += 1
        if trade < -5:
            severe_trades += 1
        if trade > 10:
            great_trades += 1
    bad_trades = round(bad_trades / len(temp_mediums)*100, 2)
    severe_trades = round(severe_trades / len(temp_mediums)*100, 2)
    great_trades = round(great_trades / len(temp_mediums)*100, 2)
    return bad_trades, severe_trades, great_trades


def get_accepted_companies(accepted_companies, timeframe, form_data):
    total_years = [2002, 2003, 2004, 2005, 2006, 2007, 2008,
                   2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    years = total_years[total_years.index(
        int(form_data["start_year"])-1):total_years.index(int(form_data["end_year"]))+1]
    companies_last_year = {}
    high_hists = {}
    medium_hists = {}
    low_hists = {}
    package_objects = {}
    breakdowns_per_year = {}
    amount_highs = [1000]
    amount_mediums = [1000]
    amount_lows = [1000]
    tax_credit_high = 0
    tax_credit_low = 0
    for year in years:
        companies = {}
        for company in accepted_companies:
            if year in company.mediums.keys():
                temp_highs = []
                temp_mediums = []
                temp_lows = []
                start_date = company.start_dates[year]
                end_date = company.end_dates[year]
                for mediums_key in company.mediums.keys():
                    if mediums_key <= year:
                        temp_highs.append(company.highs[mediums_key])
                        temp_mediums.append(company.mediums[mediums_key])
                        temp_lows.append(company.lows[mediums_key])

                average_high, average_medium, average_low = calc_average(
                    temp_highs, temp_mediums, temp_lows)
                median_high, median_medium, median_low = calc_median(
                    temp_highs, temp_mediums, temp_lows)
                bad_trades, severe_trades, great_trades = sort_trades(
                    temp_mediums)
                companies[company.id] = Company(company.ticker, company.name, company.id, average_high, average_medium, average_low,
                                                median_high, median_medium, median_low, bad_trades, severe_trades, great_trades, start_date, end_date)
        calc_indicator(companies, form_data)
        if year == years[0]:
            companies_last_year = companies
        elif year == years[1]:
            amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high, tax_credit_low = packages.expert_get_firms_from_db(
                companies_last_year, companies, timeframe, year, amount_highs[-1], amount_mediums[-1], amount_lows[-1], tax_credit_high, tax_credit_low)
            companies_last_year = companies

            high_hists[year] = high_hist
            medium_hists[year] = medium_hist
            low_hists[year] = low_hist

            package_objects[year] = package_object
            breakdowns_per_year[year] = backtest_breackdowns

            amount_highs.append(amount_high)
            amount_mediums.append(amount_medium)
            amount_lows.append(amount_low)
        else:
            amount_high, amount_medium, amount_low, last_date, high_hist, medium_hist, low_hist, package_object, backtest_breackdowns, tax_credit_high, tax_credit_low = packages.expert_get_firms_from_db(
                companies_last_year, companies, timeframe, year, amount_highs[-1], amount_mediums[-1], amount_lows[-1], tax_credit_high, tax_credit_low, last_date)
            companies_last_year = companies

            high_hists[year] = high_hist
            medium_hists[year] = medium_hist
            low_hists[year] = low_hist

            package_objects[year] = package_object
            breakdowns_per_year[year] = backtest_breackdowns

            amount_highs.append(amount_high)
            amount_mediums.append(amount_medium)
            amount_lows.append(amount_low)

    return high_hists, medium_hists, low_hists, package_objects, breakdowns_per_year
