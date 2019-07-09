import sqlite3
import csv


def get_db_ticker():
    db_connection = sqlite3.connect('databases/div_trade_v8b.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Ticker FROM Companies")
    db_ticker = db_cursor.fetchall()
    db_connection.close()
    total_ticker = []
    for ticker in db_ticker:
        ticker = ticker[0]
        if "." in ticker:
            ticker = ticker[:ticker.index(".")]
        total_ticker.append(ticker)
    return total_ticker

def get_earnings_ticker():
    with open("earnings_calendar_data.csv", "r") as earnings_calender:
        table=csv.reader(earnings_calender)
        earnings_ticker = []
        for row in table:
            ticker = row[0]
            if "." in ticker:
                ticker = ticker[:ticker.index(".")]
            earnings_ticker.append(ticker)
        return earnings_ticker

def compare_db_and_earnings_ticker():
    db_ticker = get_db_ticker()
    earnings_ticker = get_earnings_ticker()
    overlapping = []
    not_overlapping = []
    for ticker in db_ticker:
        if ticker in earnings_ticker:
            overlapping.append(ticker)
        if ticker not in earnings_ticker:
            not_overlapping.append(ticker)
    print("original")
    print(len(db_ticker))
    print("overlapping")
    print(len(overlapping))
    print("not overlapping")
    print(len(not_overlapping))
    return not_overlapping, 

print(compare_db_and_earnings_ticker())