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

x = "2019/04/02"

y=x.split("/")
v = date(int(y[0]),int(y[1]),int(y[2]))
print(v)

blub = v - timedelta(days=-32)
print(blub)