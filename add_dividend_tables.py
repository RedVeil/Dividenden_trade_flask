import sqlite3

db_connection = sqlite3.connect('databases/div_trade_v9c.db')
db_cursor = db_connection.cursor()
years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008,
                   2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
for year in years:
    db_cursor.execute(f"""CREATE TABLE "dividends_{year}" 
                        ("ID" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "Company_ID" INTEGER NOT NULL,
                        "Index" INTEGER NOT NULL,
                        "Date" TEXT NOT NULL,
                        "Amount" INTEGER NOT NULL,
                        "Percent" INTEGER NOT NULL)""")
db_connection.commit()
db_cursor.close()
