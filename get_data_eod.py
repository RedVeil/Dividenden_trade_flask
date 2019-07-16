import requests
import csv
import sqlite3
import json


class Day:
    def __init__(self, date, high, low, close, volume):
        self.date = date
        self.high = float(high)
        self.low = float(low)
        self.average = round((self.high + self.low)/2, 2)
        self.close = (float(close))
        self.volume = volume

class Company:
    def __init__(self, name, ticker, exchange, currency):
        self.name = name
        self.ticker = ticker
        self.currency = currency
        self.exchange = exchange
        self.days = []
        self.dividends = {}

    def get_sell_prices(self, index, timeframe):
        if timeframe == 0:
            date = self.days[index].date
            high = round(float(self.currency_conversion(
                self.days[index].high, date)), 2)
            low = round(float(self.currency_conversion(
                self.days[index].low, date)), 2)
            average = round((high+low)/2, 2)
        else:
            sell_index = index + timeframe
            if sell_index >= len(self.days):
                sell_index = len(self.days)-1
            sell_day = self.days[sell_index]
            date = sell_day.date
            high = round(
                float(self.currency_conversion(sell_day.high, date)), 2)
            low = round(
                float(self.currency_conversion(sell_day.low, date)), 2)
            average = round((high+low)/2, 2)
        return high, average, low, date

    def get_buy_prices(self, index, timeframe):
        buy_index = index - timeframe
        if buy_index < 0:
            buy_index = 0
        buy_day = self.days[buy_index]
        date = buy_day.date
        high = buy_day.high
        low = buy_day.low
        average = buy_day.average
        return high, average, low, date

    def calculate_dividend_percentage(self, year, n):
        ex_day = self.get_day_by_date(self.dividends[year][n]["date"])
        if ex_day != "pop":
            dividend_percentage = round(float(self.dividends[year][n]["value"])/ex_day.close*100, 2)
            self.dividends[year][n]["percent"] = dividend_percentage
        

    def convert_other_currency(self, historic_data, dividend_data):
        with open(f"currencies/foreign-eur/{self.currency}EUR.FOREX.csv", "r") as currency_data:
            table = csv.reader(currency_data)
            conversions = {}
            for row in table:
                date = row[0]
                close = row[4]
                conversions[date] = close
            for i in historic_data:
                if i["high"] != 0 and i["low"] != 0 and i["close"]!= 0:
                    if i["date"] in conversions.keys():
                        converted_high = round(
                            float(conversions[i["date"]])*float(i["high"]), 2)
                        converted_low = round(
                            float(conversions[i["date"]])*float(i["low"]), 2)
                        converted_close = round(
                            float(conversions[i["date"]])*float(i["close"]), 2)
                        self.days.append(Day(i["date"], converted_high, converted_low, converted_close, i["volume"]))


            for i in dividend_data:
                if dividend_data[i]["date"] in conversions.keys():
                    converted_value = round(
                        float(conversions[dividend_data[i]["date"]])*float(dividend_data[i]["value"]), 2)
                    year = dividend_data[i]["date"][0:4]
                    if year not in self.dividends.keys():
                            self.dividends[year] = [{"date": dividend_data[i]["date"], "value": converted_value}]
                    else:
                        self.dividends[year].append({"date": dividend_data[i]["date"], "value": converted_value})

    def convert_ils(self, historic_data, dividend_data):
        with open(f"currencies/foreign-eur/ILS.FOREX.csv", "r") as currency_data:
            ils_table = csv.reader(currency_data)
            conversions_ils = {}
            for row in ils_table:
                date = row[0]
                close = row[4]
                conversions_ils[date] = close
            for i in historic_data:
                if i["date"] in conversions_ils.keys():
                    if i["high"] != 0 and i["low"] != 0 and i["close"]!= 0:
                        converted_high = round(float(conversions_ils[i["date"]])*float(i["high"]), 2)
                        converted_low = round(float(conversions_ils[i["date"]])*float(i["low"]), 2)
                        converted_close = round(float(conversions_ils[i["date"]])*float(i["close"]), 2)
                        with open(f"currencies/foreign-eur/USDEUR.FOREX.csv", "r") as us_currency_data:
                            usd_table = csv.reader(us_currency_data)
                            conversions_usd = {}
                            for row in usd_table:
                                date = row[0]
                                close = row[4]
                                conversions_usd[date] = close
                            final_converted_high = round(float(conversions_usd[i["date"]])*float(converted_high), 2)
                            final_converted_low = round(float(conversions_usd[i["date"]])*float(converted_low), 2)
                            final_converted_close = round(float(conversions_usd[i["date"]])*float(converted_close), 2)
                            self.days.append(Day(i["date"], final_converted_high, final_converted_low, final_converted_close, i["volume"]))

            for i in dividend_data:
                if dividend_data[i]["date"] in conversions_ils.keys():
                    converted_value = round(
                        float(conversions_ils[dividend_data[i]["date"]])*float(dividend_data[i]["value"]), 2)
                    with open(f"currencies/foreign-eur/USDEUR.FOREX.csv", "r") as us_currency_data:
                        usd_table = csv.reader(us_currency_data)
                        conversions_usd = {}
                        for row in usd_table:
                            date = row[0]
                            close = row[4]
                            conversions_usd[date] = close
                        final_converted_value = round(float(conversions_usd[dividend_data[i]["date"]])*float(converted_value), 2)
                        year = dividend_data[i]["date"][0:4]
                        if year not in self.dividends.keys():
                            self.dividends[year] = [{"date": dividend_data[i]["date"], "value": final_converted_value}]
                        else:
                            self.dividends[year].append({"date": dividend_data[i]["date"], "value": final_converted_value})


    def currency_conversion(self, historic_data, dividend_data):
        if self.currency != "EUR" and self.currency != "ILS":
            self.convert_other_currency(historic_data, dividend_data)
        if self.currency == "ILS":
            pass
            #self.convert_ils(historic_data, dividend_data)
        if self.currency == "EUR":
            for i in historic_data:
                if i["high"] != 0 and i["low"] != 0 and i["close"]!= 0:
                    self.days.append(
                        Day(i["date"], i["high"], i["low"], i["close"], i["volume"]))
            for i in dividend_data:
                year = dividend_data[i]["date"][0:4]
                if year not in self.dividends.keys():
                    self.dividends[year] = [{"date": dividend_data[i]["date"], "value": dividend_data[i]["value"]}]
                else:
                    self.dividends[year].append({"date": dividend_data[i]["date"], "value": dividend_data[i]["value"]})

    def get_day_by_date(self, date):
        for index in range(len(self.days)):
            if self.days[index].date == date:
                return self.days[index]
        return "pop"


def write_dividends_to_db(name, dividends):
    db_connection = sqlite3.connect('databases/div_trade_v9.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"SELECT ID FROM '01_Companies' WHERE Name = '{name}'")
    company_id = db_cursor.fetchone()
    company_id = company_id[0]
    for year in dividends.keys():
        for i in range(len(dividends[year])):
            try:
                db_cursor.execute(f"""INSERT INTO 'dividends_{year}' ('Company_ID', 'Index', 'Date', 'Amount', 'Percent') 
                            VALUES ('{company_id}','{i}','{dividends[year][i]["date"]}','{dividends[year][i]["value"]}','{dividends[year][i]["percent"]}')""")
            except KeyError:
                pass
    db_connection.commit()
    db_cursor.close()
    print(f"{name} dividends added")

def write_historic_data_to_db(ticker, days):
    db_connection = sqlite3.connect('databases/div_trade_v9.db')
    db_cursor = db_connection.cursor()
    try:
        db_cursor.execute(f"""CREATE TABLE "{ticker}" 
                        ("ID" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "Date" TEXT NOT NULL,
                        "High" INTEGER NOT NULL,
                        "Low" INTEGER NOT NULL,
                        "Close" INTEGER NOT NULL,
                        "Volume" INTEGER)""")
    except sqlite3.OperationalError:
        pass
    db_connection.commit()
    for day in days:
        db_cursor.execute(f"INSERT INTO '{ticker}' (Date, High, Low, Close, Volume) VALUES ('{day.date}','{day.high}','{day.low}','{day.close}','{day.volume}')")
    db_connection.commit()
    db_cursor.close()
    print(f"{ticker} table added")

def write_company_to_db(name, ticker, exchange, currency):
        db_connection = sqlite3.connect('databases/div_trade_v9.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(
            f"SELECT Name FROM '01_Companies' WHERE Name = '{name}'")
        company = db_cursor.fetchone()
        if not company:
            db_cursor.execute(
                f"INSERT INTO '01_Companies' (Name, Ticker, Exchange, Currency) VALUES ('{name}', '{ticker}', '{exchange}','{currency}')")
        db_connection.commit()
        db_cursor.close()
        print(f"{ticker} added to companies")

def initial_filter(historic_data, dividend_data, company):
    if type(dividend_data) != dict:
        print("dict")
        return False
    try:
        x = float(historic_data[-1]["close"])*0.5
    except TypeError:
        print("historic")
        return False
    try:
        y = float(dividend_data["1"]["value"])*0.5
    except TypeError:
        print("dividend")
        return False
    except KeyError:
        print(dividend_data)
    if company.currency == "USD" or company.currency == "CAD":
        if len(dividend_data.keys()) < 20:
            print("not enough dividends")
            return False
    if len(dividend_data.keys()) < 5:
        print("not enough dividends")
        return False
    for i in historic_data:
        if type(i) != dict:
            print("historic i not dict")
            return False
    else:
        return True

def get_historic_data(ticker, api_token, params):
    session = requests.Session()
    url_historic = f"https://eodhistoricaldata.com/api/eod/{ticker}?api_token={api_token}&fmt=json"
    reponse_historic = session.get(url_historic, params=params)
    if reponse_historic.status_code == requests.codes.ok:
        historic_data = json.loads(reponse_historic.text)
        return historic_data
    else:
        print(f"{ticker} historic status problem")


def get_dividend_data(ticker, api_token, params):
    session = requests.Session()
    url_dividends = f"https://eodhistoricaldata.com/api/div/{ticker}?api_token={api_token}&from=2000-01-01&fmt=json"
    reponse_dividends = session.get(url_dividends, params=params)
    if reponse_dividends.status_code == requests.codes.ok:
        dividend_data = json.loads(reponse_dividends.text)
        return dividend_data
    else:
        print(f"{ticker} dividend status problem")

def get_eod_data(eod_ticker, api_token):
    params = {"api_token": api_token}
    historic_data = get_historic_data(eod_ticker, api_token, params)
    dividend_data = get_dividend_data(eod_ticker, api_token, params)
    return historic_data, dividend_data

def get_ticker(api_token):
    exchange_codes={"US":"US",} #done: ("GER":"XETRA","LUX":"LU","DEN":"CO","AT":"VI","SP":"MC","FR":"PA","CHF":"VX","CA":"TO", "IT":"MI","SWE":"ST","NOR":"OL","UK":"LSE", ) /to_do:
    session = requests.Session()
    params = {"api_token": api_token}
    companies = {}
    for key in exchange_codes.keys():
        print(f"geting ticker from {exchange_codes[key]}")
        url_exchange= f"https://eodhistoricaldata.com/api/exchanges/{exchange_codes[key]}?api_token={api_token}&fmt=json"
        reponse_exchange = session.get(url_exchange, params=params)
        if reponse_exchange.status_code == requests.codes.ok:
            print("status ok")
            exchange_data = json.loads(reponse_exchange.text)
            for item in exchange_data:
                if item["Type"] == "Common Stock" and item["Code"] not in companies.keys():
                    currency = item["Currency"]
                    if currency == "GBX":
                        currency = "GBP"
                    exchange = item["Exchange"]
                    if currency == "USD":
                        exchange = "US"
                    name = item["Name"]
                    if name != None:
                        if "'" in name:
                            name = name.replace("'", "")
                        company = Company(name, item["Code"], exchange, currency)
                        companies[item["Code"]] = company
    return companies


if __name__ == "__main__":
    api_token = "5d19ac0dbbdd85.51123060"
    companies = get_ticker(api_token)
    print(len(companies))
    bans = ['A', 'AACAF', 'AAL', 'AAN', 'AAON', 'AAP', 'AAPL', 'AAT', 'AAVVF', 'AB', 'ABBV', 'ABC', 'ABCB', 'ABDC', 'ABEV', 'ABM', 'ABR', 'ABRTY', 'ABSSF', 'ABT', 'ACC', 'ACDSF', 'ACET', 'ACI', 'ACMC', 'ACN', 'ACNB', 'ACP', 'ACRE', 'ACU', 'ACV', 'ADBE', 'ADC', 'ADI', 'ADKT', 'ADP', 'ADRNY', 'ADSK', 'ADTN', 'ADWPF', 'ADX', 'AE', 'AEB', 'AED', 'AEE', 'AEH', 'AEO', 'AEP', 'AES', 'AFAP', 'AFB', 'AFC', 'AFG', 'AFL', 'AFT', 'AGCO', 'AGD', 'AGLNF', 'AGM', 'AGN', 'AGNC', 'AGO', 'AGRPY', 'AGYS', 'AHC', 'AHH', 'AHT', 'AI', 'AILIH', 'AIMC', 'AIN', 'AINV', 'AIR', 'AIT', 'AIV', 'AIZ', 'AJG', 'AKO-A', 'AKP', 'AKR', 'AKS', 'AKZOF', 'AL', 'ALB', 'ALBY', 'ALCO', 'ALE', 'ALEX', 'ALG', 'ALGT', 'ALK', 'ALL', 'ALLE', 'ALOT', 'ALPVN', 'ALRS', 'ALSK', 'ALSN', 'ALX', 'AMBK', 'AMC', 'AMCRY', 'AME', 'AMEN', 'AMFC', 'AMH', 'AMID', 'AMJL', 'AMNB', 'AMNF', 'AMOT', 'AMOV', 'AMP', 'AMRB', 'AMSF', 'AMSWA', 'AMT', 'AMTD', 'AMTPQ', 'AMWD', 'ANAT', 'ANDE', 'ANDX', 'ANF', 'ANH', 'ANTM', 'ANZBY', 'AOD', 'AON', 'AOS', 'AP', 'APA', 'APAM', 'APC', 'APD', 'APEMY', 'APEX', 'APH', 'APL', 'APLE', 'APLO', 'APO', 'APOG', 'APTL',
            'APTS', 'APTV', 'APU', 'ARCAY', 'ARCB', 'ARCC', 'ARE', 'ARES', 'ARGO', 'ARI', 'ARKR', 'ARLP', 'ARMK', 'ARNC', 'AROC', 'AROW', 'ARR', 'ARTNA', 'ASA', 'ASB', 'ASFI', 'ASG', 'ASH', 'ASRV', 'ASRVP', 'ASTE', 'ATAX', 'ATEYY', 'ATGE', 'ATI', 'ATLO', 'ATNI', 'ATO', 'ATR', 'ATRI', 'AU', 'AUB', 'AUBN', 'AVA', 'AVAL', 'AVB', 'AVD', 'AVGO', 'AVIFY', 'AVK', 'AVP', 'AVT', 'AVX', 'AVY', 'AWCMY', 'AWF', 'AWK', 'AWP', 'AWR', 'AWRRF', 'AXS', 'AYI', 'AYR', 'AZZ', 'B', 'BABB', 'BAF', 'BAH', 'BAK', 'BANC', 'BANF', 'BANFP', 'BANR', 'BANX', 'BAOB', 'BAP', 'BAX', 'BBBK', 'BBD', 'BBDC', 'BBF', 'BBGI', 'BBK', 'BBN', 'BBSI', 'BBT', 'BBY', 'BC', 'BCBP', 'BCH', 'BCO', 'BCRH', 'BCTF', 'BCX', 'BDC', 'BDGE', 'BDJ', 'BDN', 'BDORY', 'BDVSY', 'BDX', 'BEBE', 'BELFA', 'BEN', 'BERK', 'BF-A', 'BFC', 'BFGIF', 'BFIN', 'BFK', 'BFO', 'BFS', 'BFY', 'BFZ', 'BG', 'BGCP', 'BGFV', 'BGG', 'BGH', 'BGIO', 'BGR', 'BGS', 'BGT', 'BGX', 'BGY', 'BHB', 'BHGE', 'BHK', 'BHKLY', 'BHLB', 'BHR', 'BHRB', 'BHV', 'BHWB', 'BID', 'BIF', 'BIG', 'BIT', 'BK', 'BKCC', 'BKE', 'BKEAY', 'BKEP', 'BKH', 'BKHYY', 'BKJ', 'BKK', 'BKN', 'BKS', 'BKSC',
            'BKT', 'BKU', 'BKUT', 'BLC', 'BLE', 'BLIAQ', 'BLK', 'BLKB', 'BLL', 'BLMC', 'BLUBF', 'BLW', 'BLX', 'BMBN', 'BME', 'BMI', 'BMRC', 'BMS', 'BMTC', 'BMYMP', 'BNY', 'BOALY', 'BOCH', 'BOE', 'BOH', 'BOKF', 'BONTQ', 'BOOM', 'BORT', 'BOTJ', 'BPFH', 'BPL', 'BPOP', 'BPOPM', 'BPOPN', 'BPT', 'BQH', 'BR', 'BRBS', 'BRC', 'BRFS', 'BRG', 'BRID', 'BRKL', 'BRKS', 'BRN', 'BRO', 'BRRAY', 'BRS', 'BRSS', 'BRT', 'BRX', 'BSAC', 'BSBR', 'BSD', 'BSE', 'BSET',
            'BSL', 'BSPA', 'BSRR', 'BTA', 'BTBIF', 'BTO', 'BTT', 'BTZ', 'BUI', 'BURCA', 'BUSE', 'BVERS', 'BVN', 'BWA', 'BWEL', 'BWG', 'BWXT', 'BX', 'BXBLY', 'BXMT', 'BXMX', 'BXP', 'BXS', 'BYD', 'BYFC', 'BYLB', 'BYM', 'BZM', 'CAC', 'CAG', 'CAH', 'CAJ', 'CAKE', 'CAL', 'CALM', 'CAPL', 'CARE', 'CARO', 'CARV', 'CASH', 'CASS', 'CASY', 'CATC', 'CATO', 'CATY', 'CAW', 'CB', 'CBAF', 'CBAN', 'CBCYB', 'CBCZ', 'CBD', 'CBFV', 'CBH', 'CBK', 'CBKM', 'CBKPP', 'CBL', 'CBM', 'CBNC', 'CBOE', 'CBRL', 'CBS', 'CBSH', 'CBT', 'CBU', 'CCBG', 'CCD', 'CCEP', 'CCFH', 'CCFN', 'CCI', 'CCL', 'CCLAY', 'CCLP', 'CCNE', 'CCOHY', 'CCOI', 'CCOJY', 'CCRK', 'CCU', 'CCUR', 'CCZ', 'CDEVY', 'CDMOP',
            'CDOR', 'CDR', 'CDW', 'CE', 'CEB', 'CECE', 'CEFC', 'CEL', 'CELP', 'CEM', 'CEO', 'CEQP', 'CESTF', 'CF', 'CFBK', 'CFFI', 'CFFN', 'CFR', 'CGIP', 'CGNX', 'CGO', 'CHBH', 'CHCO', 'CHD', 'CHE', 'CHFC', 'CHH', 'CHI', 'CHK', 'CHKR', 'CHL', 'CHMG', 'CHMI', 'CHMP', 'CHRW', 'CHS', 'CHSCN', 'CHSP', 'CHW', 'CHY', 'CI', 'CIB', 'CIBN', 'CIF', 'CIG', 'CII', 'CIM', 'CINF', 'CINR', 'CIO', 'CIOXY', 'CIR', 'CIT', 'CIVB', 'CIWV', 'CIX', 'CIZN', 'CKX', 'CL', 'CLB', 'CLC', 'CLCT', 'CLDB', 'CLDT', 'CLF', 'CLGX', 'CLI', 'CLMT', 'CLNY', 'CLPHF', 'CLX', 'CMA', 'CMC', 'CMCO', 'CMCSA', 'CMCT', 'CME', 'CMFN', 'CMI', 'CMO', 'CMP', 'CMPGY', 'CMRE', 'CMS', 'CMSQY', 'CMTL', 'CMTOY', 'CMTV', 'CMU', 'CNA', 'CNBA', 'CNBKA', 'CNI', 'CNIG', 'CNK', 'CNLHN', 'CNMD', 'CNND', 'CNO', 'CNOB', 'CNP', 'CNS', 'CNSL', 'CNX', 'CODI', 'COF', 'COFS', 'COG', 'COHN', 'COHU', 'COKE', 'COLB', 'COLM', 'CONE', 'COO',
            'COR', 'CORE', 'CORR', 'COST', 'CPA', 'CPB', 'CPCAY', 'CPF', 'CPK', 'CPKF', 'CPL', 'CPLP', 'CPSI', 'CPT', 'CPTA', 'CPTP', 'CQP', 'CR', 'CRD-A', 'CRH', 'CRI', 'CRLKP', 'CRPFY', 'CRR', 'CRS', 'CRT', 'CRWS', 'CRZY', 'CSBB', 'CSC', 'CSFL', 'CSGS', 'CSIOY', 'CSKL', 'CSL', 'CSPI', 'CSQ', 'CSQSY', 'CSS', 'CSV', 'CSVI', 'CSWC', 'CSX', 'CTAM', 'CTAS', 'CTB', 'CTBI', 'CTBK', 'CTDN', 'CTGSP', 'CTL', 'CTNR', 'CTO', 'CTPZY', 'CTR', 'CTRE', 'CTS', 'CTT', 'CTWS', 'CTY', 'CTYP', 'CUB', 'CUBE', 'CULP', 'CUUHF', 'CUZ', 'CVA', 'CVBF', 'CVCY', 'CVI', 'CVLY', 'CVR', 'CVS', 'CW', 'CWBC', 'CWCO', 'CWPS', 'CWT', 'CXDO', 'CXE', 'CXH', 'CXP', 'CXW', 'CY', 'CYCCP', 'CYD',
            'CYFL', 'CYVF', 'CZBT', 'CZFS', 'CZNC', 'CZNL', 'CZWI', 'D', 'DAKT', 'DAL', 'DAN', 'DBCP', 'DBD', 'DBI', 'DBL', 'DBSDY', 'DCF', 'DCI', 'DCIX', 'DCMYY', 'DCOM', 'DCP', 'DD', 'DDF', 'DDR', 'DDS', 'DDT', 'DE', 'DEI', 'DELTY', 'DEST', 'DEX', 'DF', 'DFIHY', 'DFP', 'DFS', 'DGICA', 'DGRLY', 'DGX', 'DHCPQ', 'DHF', 'DHI', 'DHR', 'DHT', 'DIMC', 'DIN', 'DIT', 'DK', 'DKL', 'DKS', 'DKT', 'DLA', 'DLB', 'DLNG', 'DLR', 'DLX', 'DMB', 'DMLP', 'DMO',
            'DNBF', 'DNI', 'DNKN', 'DNP', 'DNPLY', 'DO', 'DOC', 'DOMR', 'DOV', 'DOX', 'DPG', 'DPM', 'DPZ', 'DRAD', 'DRE', 'DRH', 'DRI', 'DRL', 'DRYS', 'DS', 'DSE', 'DSEEY', 'DSFN', 'DSM', 'DSWL', 'DSX-PB', 'DTE', 'DTF', 'DTRL', 'DUC', 'DUK', 'DVCR', 'DVD', 'DVN', 'DWAHY', 'DWDP', 'DWNX', 'DX', 'DXB', 'DXC', 'DXR', 'EAB', 'EAE', 'EARN', 'EAT', 'EBF', 'EBIX', 'EBMT', 'EBTC', 'ECC', 'ECL', 'ECOL', 'ECT', 'ED', 'EDD', 'EDF', 'EDI', 'EDPFY', 'EDUC', 'EE', 'EEA', 'EEI', 'EFC', 'EFF', 'EFIN', 'EFL', 'EFR', 'EFSC', 'EFSI', 'EFT', 'EFX', 'EGF', 'EGIEY', 'EGIF', 'EGOV', 'EGP', 'EHC', 'EHI', 'EHT', 'EIG', 'EIX', 'EL', 'ELMA', 'ELP', 'ELS', 'ELSE', 'ELU', 'ELY', 'EMCF', 'EMCI', 'EMD', 'EME', 'EMF', 'EML', 'EMN', 'EMO', 'EMR', 'ENBL', 'ENBP', 'ENDTF', 'ENIA', 'ENJ', 'ENLC', 'ENS', 'ENSG', 'EOCCY', 'EOD', 'EOG', 'EOI', 'EOS', 'EOT', 'EPD', 'EPM', 'EPR', 'EQC', 'EQIX', 'EQM', 'EQR', 'EQT', 'ERIE', 'ERJ', 'ES', 'ESALY', 'ESBA', 'ESCA', 'ESCSQ', 'ESE', 'ESEA', 'ESLT', 'ESP', 'ESRT', 'ESS', 'ESSA', 'ESV', 'ET', 'ETB', 'ETG', 'ETH', 'ETJ', 'ETM', 'ETN', 'ETO', 'ETR', 'ETV', 'ETW', 'ETY', 'EUIVF', 'EV', 'EVBN', 'EVC', 'EVF', 'EVG', 'EVN', 'EVOL', 'EVR', 'EVRG', 'EVT', 'EVTC', 'EWBC', 'EXC', 'EXCOF', 'EXD', 'EXETF', 'EXG', 'EXP', 'EXPD', 'EXPE', 'EXPO', 'EXR', 'FABK', 'FABP', 'FAF', 'FAM', 'FAME', 'FARM', 'FAST', 'FBAK', 'FBASF', 'FBC', 'FBHS', 'FBIP', 'FBIZ', 'FBMS', 'FBNC', 'FBP', 'FBPI', 'FBPRL', 'FBPRP', 'FBSI', 'FBSS', 'FBTT', 'FBVA', 'FCAP', 'FCBC', 'FCBI', 'FCCG', 'FCCO', 'FCF', 'FCNCA', 'FCRGF', 'FCT', 'FCX', 'FDBC', 'FDEF',
            'FDEU', 'FDP', 'FDS', 'FDUS', 'FE', 'FEI', 'FETM', 'FF', 'FFA', 'FFBC', 'FFC', 'FFDF', 'FFG', 'FFIC', 'FFIN', 'FFNW', 'FFWC', 'FGB', 'FGBI', 'FGFH', 'FGP', 'FHN', 'FIBH', 'FIBK', 'FICO', 'FIF', 'FII', 'FINN', 'FIS', 'FISI', 'FITB', 'FIV', 'FIX', 'FIZN', 'FJTSY', 'FKYS', 'FL', 'FLC', 'FLEW', 'FLIC', 'FLIR', 'FLO', 'FLR', 'FLS', 'FLXS', 'FLY', 'FMAO', 'FMBH', 'FMBI', 'FMBL', 'FMBM', 'FMC', 'FMCB', 'FMCC', 'FMCKK', 'FMFG', 'FMN', 'FMNB', 'FMO', 'FMX', 'FMY', 'FNB', 'FNCB', 'FNF', 'FNFI', 'FNHC', 'FNLC', 'FNLIF', 'FNMA', 'FOE', 'FOF', 'FORR', 'FOX', 'FPAFY', 'FPF', 'FPI', 'FPL', 'FR', 'FRA', 'FRAF', 'FRC', 'FRD', 'FRED', 'FREVS', 'FRFC', 'FRFGF', 'FRME', 'FRT', 'FSBW', 'FSCR', 'FSD', 'FSDK', 'FSFG', 'FSK', 'FSP', 'FSS', 'FST', 'FSTR', 'FT', 'FTDL', 'FTR', 'FUJHY', 'FUJIF', 'FUL', 'FULT', 'FUN', 'FUNC', 'FUND', 'FUSB', 'FWRD', 'FXLG', 'FXNC', 'GAB', 'GABC', 'GAIN', 'GAM', 'GARS', 'GAS', 'GATX', 'GBAB', 'GBCI', 'GBDC', 'GBL', 'GBNXF', 'GBOOY', 'GBX', 'GCAP', 'GCBC', 'GCCO', 'GCHOY', 'GCV', 'GD', 'GDL', 'GDO', 'GDV', 'GECC', 'GEF', 'GEL', 'GEO', 'GES', 'GF', 'GFED', 'GFF', 'GFI',
            'GFNCP', 'GFY', 'GG', 'GGB', 'GGG', 'GGM', 'GGN', 'GGT', 'GHC', 'GHL', 'GHM', 'GHY', 'GIFI', 'GIL', 'GIM', 'GIVSY', 'GJH', 'GJO', 'GJR', 'GJS', 'GJT', 'GLAD', 'GLAE', 'GLBZ', 'GLDD', 'GLNG', 'GLNV', 'GLOG', 'GLOP', 'GLP', 'GLPI', 'GLT', 'GLW', 'GM', 'GMBXF', 'GME', 'GMLP', 'GMZ', 'GNBF', 'GNC', 'GNE', 'GNL', 'GNT', 'GNTX', 'GOF', 'GOOD', 'GORO', 'GOVB', 'GPC', 'GPI', 'GPM', 'GPN', 'GPOVY', 'GPRE', 'GPS', 'GPTGF', 'GRC', 'GRIF', 'GRMN', 'GROW', 'GRRB', 'GRX', 'GSBC', 'GSH', 'GT', 'GTMEF', 'GTN', 'GTPS', 'GTY', 'GULRY', 'GUT', 'GVA', 'GVFF', 'GWW', 'GYB', 'GYC', 'GZT', 'HABC', 'HAFC', 'HARL', 'HAS', 'HASI', 'HAWEL', 'HAWEM', 'HAWEN', 'HAWLL', 'HAWLN', 'HAYN', 'HBAN', 'HBI', 'HBNC', 'HBSI', 'HCAP', 'HCBC', 'HCBN', 'HCFT', 'HCI', 'HCKG', 'HCP', 'HCSG', 'HE', 'HEES', 'HEI', 'HEP', 'HEQ', 'HES', 'HFBA', 'HFBC', 'HFBK', 'HFBL', 'HFC', 'HFRO', 'HFWA', 'HGH', 'HGKGY',
            'HGTXU', 'HHILY', 'HHS', 'HI', 'HIE', 'HIFS', 'HIG', 'HIHO', 'HII', 'HIO', 'HIW', 'HIX', 'HKHHF', 'HL', 'HLAN', 'HLDCY', 'HLF', 'HLFN', 'HLM-P', 'HLPPY', 'HMC', 'HMLN', 'HMN', 'HMNF', 'HNFSA', 'HNI', 'HNNA', 'HNP', 'HNRG', 'HOCPY', 'HOFT', 'HOKCY', 'HOMB', 'HON', 'HONT', 'HOPE', 'HOWWY', 'HP', 'HPF', 'HPI', 'HPP', 'HPS', 'HPT', 'HQH', 'HQL', 'HR', 'HRB', 'HRC', 'HRCR', 'HRL', 'HRS', 'HRUFF', 'HRZN', 'HSC', 'HSII', 'HSNGF', 'HST', 'HSY', 'HT', 'HTA', 'HTBK', 'HTD', 'HTGC', 'HTHIY', 'HTLD', 'HTLF', 'HTY', 'HUBB', 'HUM', 'HUN', 'HURC', 'HVT', 'HWBK', 'HWC', 'HWCC', 'HWEN', 'HWKN', 'HY', 'HYB', 'HYI', 'IAE', 'IAUGY', 'IBA', 'IBCP', 'IBKC', 'IBKR', 'IBM', 'IBN', 'IBOC', 'IBTX', 'ICE', 'ICL', 'ICTPU', 'IDA', 'IDCC', 'IDE', 'IDT', 'IDWM', 'IEP', 'IESFY', 'IEX', 'IFF', 'IFN', 'IGA', 'IGD', 'IGI', 'IGR', 'IHC', 'IHD', 'IHIT', 'IHLDY', 'IHT', 'IID', 'IIF', 'IIIN', 'IIJI', 'IIM', 'IMH', 'IMKTA', 'IMPUY', 'INB', 'INBK', 'INDB', 'INF', 'INFY', 'INGR', 'INN', 'INPAP', 'INSI', 'INT', 'INTC', 'INTU', 'IOCJY', 'IOFB', 'IOOXF', 'IOSP', 'IP', 'IPAR', 'IPB', 'IPG', 'IPHS', 'IPWLK', 'IPWLP', 'IQI', 'IR', 'IRCP', 'IRET', 'IRL', 'IRM', 'IRR', 'IRSHF', 'IRT', 'ISARF', 'ISBA', 'ISBC', 'ISCA', 'ISD', 'ISF', 'ISG', 'ISTR', 'ITC', 'ITEX', 'ITIC', 'ITRN', 'ITT', 'ITUB', 'ITW', 'IVC', 'IVH', 'IVR', 'IVZ', 'IX', 'JACK', 'JBHT', 'JBK', 'JBL', 'JBN', 'JBT', 'JCE', 'JCI', 'JCOM', 'JCP', 'JCS', 'JDD', 'JDVB', 'JEF', 'JEMD', 'JFBC', 'JFR', 'JFWV', 'JGH', 'JHB', 'JHD', 'JHI', 'JHS', 'JHX', 'JHY', 'JJSF', 'JKHY', 'JLL', 'JLS', 'JMF', 'JMHLY', 'JMLP', 'JMM', 'JMP', 'JMPB', 'JMT', 'JNES', 'JNJ', 'JNPR', 'JOE', 'JOUT', 'JPC', 'JPI', 'JPM-PA', 'JPS', 'JPT', 'JQC', 'JRI', 'JRO', 'JRS', 'JSD', 'JSHLY', 'JSM', 'JTA', 'JTD', 'JTNB', 'JUVF', 'JW-A', 'JWA', 'JWN', 'KAI', 'KALU', 'KAMN', 'KAR', 'KBAL', 'KBH', 'KBR', 'KCAP', 'KCDMF', 'KCLI', 'KDP', 'KEFI', 'KELYA', 'KEQU', 'KEWL', 'KEY', 'KFFB', 'KFRC', 'KIDBQ', 'KIM', 'KINS', 'KIO', 'KISB', 'KKR', 'KLAC', 'KLBAY', 'KLKBY', 'KMB', 'KMI', 'KMPR', 'KMR', 'KMT', 'KMTUY', 'KNBWY', 'KNL', 'KNMCY', 'KNOP', 'KNX', 'KOF', 'KOP', 'KOSS', 'KPELY', 'KR', 'KRC', 'KREVF', 'KRG', 'KRNY', 'KRO', 'KSBI', 'KSM', 'KSS', 'KSU', 'KTF', 'KTH', 'KTHN', 'KTN', 'KTP', 'KTWIF', 'KTYB', 'KW', 'KWR', 'KYN', 'KYOCY', 'L', 'LAACZ', 'LABL', 'LAD', 'LAMR', 'LANC', 'LAND', 'LARK', 'LAWS', 'LAZ', 'LB', 'LBAI', 'LBCP', 'LBY', 'LCNB', 'LCUT', 'LDOS', 'LDP', 'LEA', 'LECO', 'LEE', 'LEG', 'LEN', 'LEO', 'LEU', 'LFGP', 'LFUGY', 'LFUS', 'LGCY', 'LGI', 'LIFZF', 'LII', 'LINS', 'LION', 'LKFN', 'LLESY', 'LLL', 'LM', 'LMAT', 'LMNR', 'LNC', 'LNN', 'LNT', 'LNVGY', 'LOAN', 'LOGN', 'LOR', 'LOW', 'LPLA', 'LPMDF', 'LPT', 'LPX', 'LRCX', 'LSBK', 'LSFG', 'LSI', 'LSTR', 'LTC', 'LTKBF', 'LTM', 'LTXB', 'LUKOY', 'LUV', 'LXFR', 'LXP', 'LYB', 'LYBC', 'LYTS', 'LZB', 'LZRFY', 'M', 'MAA', 'MAC', 'MAIN', 'MAN', 'MANT', 'MAPIF', 'MAR', 'MARPS', 'MAS', 'MAT', 'MATW', 'MATX', 'MAURY', 'MAV', 'MBCN', 'MBFI', 'MBI', 'MBKL', 'MBT', 'MBTF', 'MBWM', 'MC', 'MCA', 'MCBC', 'MCC', 'MCEM', 'MCHB', 'MCHP', 'MCHX', 'MCI', 'MCK', 'MCN', 'MCO', 'MCPH', 'MCR', 'MCRAA', 'MCS', 'MCV', 'MCY', 'MDC', 'MDCA', 'MDLZ', 'MDP', 'MDU', 'MDVT', 'MEI', 'MELI', 'MEN', 'MET', 'MFA', 'MFBP', 'MFD', 'MFG', 'MFGI', 'MFIN', 'MFL', 'MFM', 'MFNC', 'MFO', 'MFSF', 'MFT', 'MFV', 'MGEE', 'MGF', 'MGPI', 'MGRC', 'MGU', 'MHD', 'MHE', 'MHF', 'MHGU', 'MHI', 'MHLD', 'MHN', 'MHO', 'MIC', 'MIE', 'MIELY', 'MIN', 'MINI', 'MITSY', 'MITT', 'MIY', 'MKC', 'MKSI', 'MKTX', 'MLAB', 'MLCO', 'MLGF', 'MLHR', 'MLI', 'MLLGF', 'MLM', 'MLR', 'MLYBY', 'MMAC', 'MMC', 'MMD', 'MMLP', 'MMM', 'MMP', 'MMS', 'MMT', 'MMTRS', 'MMU', 'MN', 'MNAT', 'MNBC', 'MNBP', 'MNE', 'MNI', 'MNOIY', 'MNP', 'MNR', 'MNRO', 'MOD', 'MOFG', 'MORN', 'MOS', 'MOV', 'MPA', 'MPB', 'MPC', 'MPLX', 'MPV', 'MPW', 'MPWR', 'MPX', 'MQBKY', 'MQT', 'MQY', 'MRCC', 'MRLN', 'MRO', 'MRTI', 'MRTN', 'MRVL', 'MSA', 'MSB', 'MSBF', 'MSBHY', 'MSD', 'MSEX', 'MSI', 'MSL', 'MSM', 'MSSEL', 'MSVB', 'MTB', 'MTBCP', 'MTEX', 'MTG', 'MTN', 'MTOR', 'MTR', 'MTRN', 'MTSC', 'MTT', 'MTW', 'MTX', 'MUA', 'MUC', 'MUE', 'MUFG', 'MUH', 'MUI', 'MUJ', 'MUR', 'MUS', 'MVBF', 'MVC', 'MVF', 'MVO', 'MVT', 'MWA', 'MXCHF', 'MXCYY', 'MXF', 'MXIM', 'MYBF', 'MYC', 'MYD', 'MYE', 'MYF', 'MYI', 'MYJ', 'MYL', 'MYN', 'MZA', 'NABZY', 'NAC', 'NACB', 'NAD', 'NAN', 'NASB', 'NAT', 'NATI', 'NATR', 'NAUH', 'NAVI', 'NAZ', 'NBB', 'NBHC', 'NBL', 'NBN', 'NBR', 'NBTB', 'NC', 'NCA', 'NCB', 'NCMI', 'NCV', 'NCZ', 'NDAQ', 'NDP', 'NDSN', 'NDVLY', 'NE', 'NEA', 'NECB', 'NEE', 'NEN', 'NESW', 'NEU', 'NEV', 'NEWEN', 'NEWM', 'NEWT', 'NFBK', 'NFG', 'NFJ', 'NFPC', 'NGG', 'NGHC', 'NGL', 'NHA', 'NHC', 'NHF', 'NHI', 'NHTC', 'NI', 'NID', 'NIDB', 'NIE', 'NILSY', 'NIM', 'NIQ', 'NJDCY', 'NJR', 'NJV', 'NKG', 'NKSH', 'NKX', 'NL', 'NLSN', 'NLY', 'NM', 'NMFC', 'NMI', 'NMM', 'NMR', 'NMS', 'NMT', 'NMY', 'NMZ', 'NNA', 'NNBR', 'NNC', 'NNI', 'NNN', 'NNUTU', 'NNY', 'NOC', 'NOM', 'NORSA', 'NOV', 'NOVC', 'NP', 'NPK', 'NPN', 'NPV', 'NQP', 'NRG', 'NRGSP', 'NRIM', 'NRK', 'NRP', 'NRT', 'NRZ', 'NS', 'NSARO', 'NSARP', 'NSC', 'NSEC', 'NSL', 'NSP', 'NSS', 'NTAP', 'NTC', 'NTDOY', 'NTES',
            'NTG', 'NTP', 'NTRI', 'NTRS', 'NTTYY', 'NTX', 'NUBC', 'NUBK', 'NUE', 'NUM', 'NUO', 'NUS', 'NUV', 'NUVR', 'NUW', 'NVG', 'NWBI', 'NWE', 'NWFL', 'NWIN', 'NWL', 'NWN', 'NWYF', 'NX', 'NXC', 'NXGN', 'NXJ', 'NXN', 'NXP', 'NXQ', 'NXR', 'NXST', 'NYCB', 'NYMT', 'NYT', 'NYV', 'NZF', 'O', 'OAK', 'OC', 'OCBI', 'OCC', 'OCFC', 'OCPNY', 'OCSI', 'OCSL', 'ODC', 'OFC', 'OFED']
    print(len(bans))
    """for key in companies.keys():
        if key in bans:
            print(key)
        if key not in bans:
            company=companies[key]
            eod_ticker = f"{company.ticker}.{company.exchange}"
            historic_data, dividend_data = get_eod_data(eod_ticker, api_token)
            if initial_filter(historic_data, dividend_data, company):
                print(company.name, company.currency, company.exchange)
                company.currency_conversion(historic_data, dividend_data)
                print("currency_conversion done")
                for year in company.dividends.keys():
                    for n in range(len(company.dividends[year])):
                        company.calculate_dividend_percentage(year, n)

                write_company_to_db(company.name, company.ticker, company.exchange, company.currency)
                write_historic_data_to_db(company.ticker, company.days)
                write_dividends_to_db(company.name, company.dividends)"""

                




