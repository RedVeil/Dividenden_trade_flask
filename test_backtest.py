import math

class Backtest_Breakdown:
    def __init__(self):
        self.capital_minus_fees_high = 0
        self.capital_minus_fees_low = 0

    def add_capital_minus_fees(self, high, low):
        self.capital_minus_fees_high = round(high,2)
        self.capital_minus_fees_low = round(low,2)

class Package():
    def __init__(self):
        self.trades = []
    def add_trade(self, trade):
        self.trades.append(trade)


def backtesting(package, amount_high, amount_medium, amount_low, tax_credit_high,tax_credit_low):
    print("----------------")
    print(f"start_amount_high:{amount_high}")
    print(f"start_amount_low:{amount_low}")
    last_dates = []
    fees = 0.01  #0.01
    taxes = 0.275 #0.275
    high_hist = []
    medium_hist = []
    low_hist = []
    backtest_breackdowns = {}
    for trade in package.trades:
        print("______________________")
        backtest_breackdowns[trade[0]] = Backtest_Breakdown()
        fees_amount_high = math.ceil(amount_high*fees)
        print(f"fees_amount_high:{fees_amount_high}")
        fees_amount_low = math.ceil(amount_low*fees)
        print(f"fees_amount_low:{fees_amount_low}")
        amount_high -= round(fees_amount_high,2)
        amount_low -= round(fees_amount_low,2)
        print(f"amount_high: {amount_high}")
        print(f"amount_low: {amount_low}")
        backtest_breackdowns[trade[0]].add_capital_minus_fees(amount_high, amount_low)
        print(f"buy_low: {trade[4]}")
        print(f"buy_high: {trade[3]}")
        stocks_high = int(amount_high/trade[4])
        stocks_low = int(amount_low/trade[3])
        print(f"stocks_high: {stocks_high}")
        print(f"stocks_low: {stocks_low}")
        if stocks_high == 0:
            if amount_high*1.1 < trade[4]:
                amount_high += fees_amount_high
                unused_high = 0
            if amount_high*1.1 >= trade[4]:
                stocks_high = 1 
                amount_high = round(stocks_high*(trade[5]+trade[9]), 2)
                unused_high = 0
        else:
            unused_high = round(amount_high - (stocks_high*trade[4]),2)
            amount_high = round(stocks_high*(trade[5]+trade[9]), 2)
        
        if stocks_low == 0:
            if amount_low*1.1 < trade[3]:
                amount_low += fees_amount_low
                unused_low = 0
            if amount_low*1.1 >= trade[3]:
                stocks_low = 1
                amount_low = round(stocks_low*(trade[6]+trade[9]), 2)
                unused_low = 0
        else:
            unused_low = round(amount_low - (stocks_low*trade[3]),2)
            amount_low = round(stocks_low*(trade[6]+trade[9]), 2)
        print(f"sell_high: {round(trade[5]+trade[9],2)}")
        print(f"sell_low: {round(trade[6]+trade[9],2)}")
        print(f"amount_high after trade:{amount_high},{unused_high}")
        print(f"amount_low after trade:{amount_low},{unused_low}") 
        amount_high -= round(amount_high*fees,2)
        amount_low -= round(amount_low*fees,2)
        print(f"amount_high after fees:{amount_high}")
        print(f"amount_low after fees:{amount_low}")

        if amount_high < backtest_breackdowns[trade[0]].capital_minus_fees_high:
            tax_credit_high += round(((backtest_breackdowns[trade[0]].capital_minus_fees_high+fees_amount_high) - amount_high)*taxes,2)
            print(f"tax_credit_high: {tax_credit_high}")
            amount_high += unused_high
        else:
            print(f"tax_credit_high: {tax_credit_high}")
            taxes_high = round((amount_high - (backtest_breackdowns[trade[0]].capital_minus_fees_high+fees_amount_high))*taxes,2)
            if taxes_high < 0:
                taxes_high = 0  
            print(f"taxes_high: {taxes_high}")
            taxes_high2 = taxes_high
            taxes_high -= tax_credit_high
            tax_credit_high = round(tax_credit_high-taxes_high2,2)
            if tax_credit_high < 0:
                tax_credit_high = 0
            if taxes_high < 0:
                taxes_high = 0       
            amount_high -= taxes_high
            amount_high += unused_high

        if amount_low < backtest_breackdowns[trade[0]].capital_minus_fees_low:
            tax_credit_low += round(((backtest_breackdowns[trade[0]].capital_minus_fees_low+fees_amount_low) - amount_low)*taxes,2)
            print(f"tax_credit_low: {tax_credit_low}")
            amount_low += unused_low
        else:
            print(f"tax_credit_low: {tax_credit_low}")
            taxes_low =  round((amount_low - (backtest_breackdowns[trade[0]].capital_minus_fees_low+fees_amount_low))*taxes,2)
            if taxes_low < 0:
                taxes_low = 0  
            print(f"taxes_high: {taxes_high}")
            taxes_low2 = taxes_low
            taxes_low -= tax_credit_low
            tax_credit_low = round(tax_credit_low-taxes_low2,2)
            if tax_credit_low < 0:
                tax_credit_low = 0
            if taxes_low < 0:
                taxes_low = 0  
            amount_low -= taxes_low
            amount_low += unused_low
        print(f"amount_high after Trade: {round(amount_high,2)}")
        print(f"amount_low after Trade: {round(amount_low,2)}")
        amount_medium = round((amount_high+amount_low)/2,2)
        high_hist.append(round(amount_high,2))
        medium_hist.append(round(amount_medium,2))
        low_hist.append(round(amount_low,2))
        last_dates.append(package.trades[-1][1])

    final_amount_high = round(amount_high, 2)
    final_amount_medium = round(amount_medium, 2)
    final_amount_low = round(amount_low, 2)
    last_date = last_dates[0]

    return final_amount_high, final_amount_medium, final_amount_low, last_date, high_hist, medium_hist, low_hist, backtest_breackdowns, tax_credit_high,tax_credit_low



x = Package()
x.add_trade(["buy_data", "sell_date", "ticker", 10, 9, 11, 8, "name", 10, 0.9])
x.add_trade(["buy_data2", "sell_date2", "ticker2", 12, 5, 13, 6, "name2", 10, 1])
y = Package()
y.add_trade(["buy_data", "sell_date", "ticker", 10, 9, 11, 8, "name", 10, 0.9])
y.add_trade(["buy_data2", "sell_date2", "ticker2", 12, 5, 13, 6, "name2", 10, 1])
final_amount_high, final_amount_medium, final_amount_low, last_date, high_hist, medium_hist, low_hist, backtest_breackdowns, tax_credit_high,tax_credit_low = backtesting(x, 1000,1000,1000, 0, 0)
final_amount_high, final_amount_medium, final_amount_low, last_date, high_hist, medium_hist, low_hist, backtest_breackdowns, tax_credit_high,tax_credit_low = backtesting(y, final_amount_high, final_amount_medium, final_amount_low,tax_credit_high,tax_credit_low )


