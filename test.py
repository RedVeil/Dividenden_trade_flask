import sqlite3
from datetime import date, timedelta

def get_us_ticker():
    db_connection = sqlite3.connect('./databases/div_trade_v9.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Ticker FROM '01_Companies' WHERE Exchange = 'US'")
    us_ticker = db_cursor.fetchall()
    ticker = []
    for i in us_ticker:
        ticker.append(i[0])
    print(ticker)
x = 3.52-3.26
y = 3.61-3.23
x1 = x/3.26
y1 = y/3.23
print((x1+y1)/2)