class Backtest:
    def __init__(self, buy_date, sell_date, name,  ticker, timeframe, buy_high, buy_low, sell_high, sell_low, dividend, amount_high, amount_low):
        self.buy_date = buy_date
        self.sell_date = sell_date
        self.ticker = ticker
        self.name = name
        self.timeframe = timeframe
        self.dividend = dividend
        self.buy_high = round(buy_high,2)
        self.buy_low = round(buy_low,2)
        self.sell_high = round(sell_high,2)
        self.sell_low = round(sell_low,2)
        self.working_capital_high = round(amount_high,2)
        self.working_capital_low = round(amount_low,2)
        self.working_capital_high_minus_fees = 0
        self.working_capital_low_minus_fees = 0
        self.stocks_high = 0
        self.stocks_low = 0
        self.unused_high = 0
        self.unused_low = 0
        self.return_high = 0
        self.return_low = 0
        self.return_high_minus_fees = 0
        self.return_low_minus_fees = 0
        self.taxes_high = 0
        self.taxes_low = 0
        self.tax_credit_high = 0
        self.tax_credit_low = 0
        self.return_minus_taxes_high = 0
        self.return_minus_taxes_low = 0
        self.return_final_high = 0
        self.return_final_low = 0

    def substract_fees(self, event):
        fees = 0.01
        if event == "buy":
            self.working_capital_high_minus_fees = round(self.working_capital_high-(self.working_capital_high*fees),2)
            self.working_capital_low_minus_fees = round(self.working_capital_low-(self.working_capital_low*fees),2)
        if event == "sell":
            self.return_high_minus_fees = round(self.return_high-(self.return_high*fees),2)
            self.return_low_minus_fees = round(self.return_low-(self.return_low*fees),2)
    
    def buy_stocks(self):
        self.stocks_high = int(self.working_capital_high_minus_fees/self.buy_low)
        self.stocks_low = int(self.working_capital_low_minus_fees/self.buy_high)
        if self.stocks_high == 0:
            self.working_capital_high_minus_fees = self.working_capital_high
        if self.stocks_low == 0:
            self.working_capital_low_minus_fees = self.working_capital_low
        
    def calculate_unused(self):
        self.unused_high = round(self.working_capital_high_minus_fees-(self.stocks_high*self.buy_low),2)
        self.unused_low = round(self.working_capital_low_minus_fees-(self.stocks_low*self.buy_high),2)

    def sell_stocks(self,):
        self.return_high = round(self.stocks_high*(self.sell_high+self.dividend),2)
        self.return_low = round(self.stocks_low*(self.sell_low+self.dividend),2)

    def calculate_taxes(self, tax_credit_high, tax_credit_low):
        taxes = 0.275
        self.taxes_high = round(((self.return_high_minus_fees-self.working_capital_high_minus_fees)*taxes)-tax_credit_high,2)
        self.taxes_low = round(((self.return_low_minus_fees-self.working_capital_low_minus_fees)*taxes)-tax_credit_low,2)
        if self.taxes_high < 0:
            self.tax_credit_high = self.taxes_high*-1
            self.taxes_high = 0
        if self.taxes_low < 0:
            self.tax_credit_low = self.taxes_low*-1
            self.taxes_low = 0
        self.return_minus_taxes_high = round(self.return_high_minus_fees - self.taxes_high,2)
        self.return_minus_taxes_low = round(self.return_low_minus_fees - self.taxes_low,2)
        return self.tax_credit_high, self.tax_credit_low
    
    def add_unused(self):
        self.return_final_high = round(self.return_minus_taxes_high + self.unused_high,2)
        self.return_final_low = round(self.return_minus_taxes_low + self.unused_low,2)
        return self.return_final_high, self.return_final_low

def backtesting(timeframe, package, amount_high, amount_low, tax_credit_high, tax_credit_low):
    amount_high = amount_high
    amount_low = amount_low
    tax_credit_high = tax_credit_high
    tax_credit_low = tax_credit_low
    backtest_breakdown = []
    for trade in package:
        trade_backtest = Backtest(trade["buy_date"],trade["sell_date"], trade["name"], trade["ticker"], timeframe, 
        trade["trade"].buy_high, trade["trade"].buy_low, trade["trade"].sell_high, trade["trade"].sell_low, trade["dividend_amount"], amount_high, amount_low)
        # buy_date, sell_date, name,  ticker, timeframe, buy_high, buy_low, sell_high, sell_low, dividend, amount_high, amount_low
        trade_backtest.substract_fees("buy")
        trade_backtest.buy_stocks()
        trade_backtest.calculate_unused()
        trade_backtest.sell_stocks()
        trade_backtest.substract_fees("sell")
        tax_credit_high, tax_credit_low = trade_backtest.calculate_taxes(tax_credit_high, tax_credit_low)
        amount_high, amount_low = trade_backtest.add_unused()
        backtest_breakdown.append(trade_backtest)
    last_date = package[-1]["sell_date"]
    return last_date, amount_high, amount_low, tax_credit_high, tax_credit_low, backtest_breakdown