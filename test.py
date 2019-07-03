import requests
import pandas as pd
from pandas.compat import StringIO
import csv

ticker = "ILSEUR.FOREX"
api_token="5d19ac0dbbdd85.51123060"


def get_eod_data(symbol=ticker, api_token=api_token, session=None):
    if session == None:
        session=requests.Session()
        url= f"https://eodhistoricaldata.com/api/eod/{symbol}"
        params = {"api_token":api_token}
        r = session.get(url, params=params)
        if r.status_code == requests.codes.ok:
            writer = csv.writer(open("./test.csv", "w"), delimiter = ",")
            for row in r.text:
                writer.writerow(row)
            '''df = pd.read_csv(StringIO(r.text), skipfooter=1, parse_dates=[0], index_col=0)
            return df
        else:
            raise Exception(r.status_code, r.reason, url)'''

print(get_eod_data())