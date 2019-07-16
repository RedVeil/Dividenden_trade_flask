import requests
import json
import time

def realtime_ticker():
    api_token = "5d19ac0dbbdd85.51123060"    
    params = {"api_token": api_token}    
    session = requests.Session()
    ticker = "BDT.XETRA"
    url_realtime = f"https://eodhistoricaldata.com/api/real-time/{ticker}?api_token={api_token}&fmt=json"
    reponse_realtime = session.get(url_realtime, params=params)
    if reponse_realtime.status_code == requests.codes.ok:
        realtime_data = json.loads(reponse_realtime.text)
        print(time.ctime(int(realtime_data["timestamp"])))
        print(realtime_data)

while True:
    realtime_ticker()
    time.sleep(60)