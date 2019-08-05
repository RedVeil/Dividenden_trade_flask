import sqlite3

total_years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008,
               2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]

db_connection = sqlite3.connect('./databases/div_trade_v9c-SWE2.db')
db_cursor = db_connection.cursor()
unique_dict = {}
double_dict = {}
for year in total_years:
    print(year)
    db_cursor.execute(f"SELECT * FROM 'dividends_{year}'")
    dividends_data = db_cursor.fetchall()
    for row in dividends_data:
        if row[1] in unique_dict.keys():
            if row[2] in unique_dict[row[1]]:
                if row[1] in double_dict.keys():
                    double_dict[row[1]].append({"id":row[0], "index":row[2]})
                else:
                    double_dict[row[1]] = [{"id":row[0], "index":row[2]}]
            else:
                unique_dict[row[1]].append(row[2])
        if row[1] not in unique_dict.keys():
            unique_dict[row[1]] = [row[2]]
    
    #print(double_dict)
    #print(unique_dict)
    for key in double_dict.keys():
        for entry in double_dict[key]:
            entry_id = entry["id"]
            db_cursor.execute(f"DELETE FROM 'dividends_{year}' WHERE ID={entry_id};") #db_cursor.execute
            db_connection.commit()
    unique_dict = {}
    double_dict = {}
db_cursor.close()
    
