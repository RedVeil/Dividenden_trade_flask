import sqlite3

def get_ticker():
    db_connection = sqlite3.connect('databases/div_trade_v7.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT Ticker FROM Companies")
    total_ticker= db_cursor.fetchall()
    db_connection.close()
    for i in total_ticker:
        print(i)

get_ticker()