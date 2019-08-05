class Backtest:
    def __init__(self, buy_date, sell_date, name,  ticker, timeframe, buy_high, buy_low, buy_close, sell_high, sell_low, sell_close, dividend, amount_high, amount_low, amount_close):
        self.buy_date = buy_date
        self.sell_date = sell_date
        self.ticker = ticker
        self.name = name
        self.timeframe = timeframe
        self.dividend = dividend
        self.buy_high = round(buy_high,2)
        self.buy_low = round(buy_low,2)
        self.buy_close= round(buy_close,2)
        self.sell_high = round(sell_high,2)
        self.sell_low = round(sell_low,2)
        self.sell_close = round(sell_close,2)
        self.working_capital_high = round(amount_high,2)
        self.working_capital_low = round(amount_low,2)
        self.working_capital_close = round(amount_close,2)
        self.invest_high = 0
        self.invest_low = 0
        self.invest_close = 0
        self.high_fees = 0
        self.low_fees = 0
        self.close_fees = 0
        self.stocks_high = 0
        self.stocks_low = 0
        self.stocks_close = 0
        self.unused_high = 0
        self.unused_low = 0
        self.unused_close = 0
        self.return_high = 0
        self.return_low = 0
        self.return_close = 0
        self.return_minus_fees_high = 0
        self.return_minus_fees_low = 0
        self.return_minus_fees_close = 0
        self.return_pre_tax_high = 0
        self.return_pre_tax_low = 0
        self.return_pre_tax_close = 0
        self.taxes_high = 0
        self.taxes_low = 0
        self.taxes_close = 0
        self.tax_credit_high = 0
        self.tax_credit_low = 0
        self.tax_credit_close = 0
        self.return_minus_taxes_high = 0
        self.return_minus_taxes_low = 0
        self.return_minus_taxes_close = 0
        self.return_final_high = 0
        self.return_final_low = 0
        self.return_final_close = 0


    def substract_fees(self, event):
        fees = 0.01
        if event == "buy":
            self.high_fees = round(self.invest_high*fees,2)
            self.low_fees = round(self.invest_low*fees,2)
            self.close_fees = round(self.invest_close*fees,2)
            if self.stocks_high == 0:
                self.return_minus_fees_high = self.working_capital_high
            if self.stocks_low == 0:
                self.return_minus_fees_low = self.working_capital_low
            if self.stocks_close == 0:
                self.return_minus_fees_close = self.working_capital_close
        if event == "sell":
            self.return_minus_fees_high = round(self.return_high-(self.return_high*fees),2)
            self.return_minus_fees_low = round(self.return_low-(self.return_low*fees),2)
            self.return_minus_fees_close = round(self.return_close-(self.return_close*fees),2)
    
    def buy_stocks(self):
        fees = 0.01
        max_capital_high = round(self.working_capital_high-(self.working_capital_high*fees),2)
        max_capital_low = round(self.working_capital_low-(self.working_capital_low*fees),2)
        max_capital_close = round(self.working_capital_close-(self.working_capital_close*fees),2)
        self.stocks_high = int(max_capital_high/self.buy_low)
        self.stocks_low = int(max_capital_low/self.buy_high)
        self.stocks_close = int(max_capital_close/self.buy_close)
        self.invest_high = round(self.stocks_high*self.buy_low,2)
        self.invest_low = round(self.stocks_low*self.buy_high,2)
        self.invest_close =  round(self.stocks_close*self.buy_close,2)
  
    def calculate_unused(self):
        self.unused_high = round(self.working_capital_high-self.invest_high-self.high_fees,2)
        self.unused_low = round(self.working_capital_low-self.invest_low-self.low_fees,2)
        self.unused_close = round(self.working_capital_close-self.invest_close-self.close_fees,2)

    def sell_stocks(self, safety_margin):
        self.return_high = round(self.stocks_high*(self.sell_high*safety_margin),2)
        self.return_low = round(self.stocks_low*(self.sell_low*safety_margin),2)
        self.return_close = round(self.stocks_close*(self.sell_close*safety_margin),2)

    def add_dividend(self):
        self.return_pre_tax_high = round(self.return_minus_fees_high + (self.stocks_high*self.dividend),2)
        self.return_pre_tax_low = round(self.return_minus_fees_low + (self.stocks_low*self.dividend),2)
        self.return_pre_tax_close = round(self.return_minus_fees_close + (self.stocks_close*self.dividend),2)

    def calculate_taxes(self, tax_credit_high, tax_credit_low, tax_credit_close):
        taxes = 0.25
        self.taxes_high = round(((self.return_pre_tax_high-self.invest_high-self.high_fees)*taxes)-tax_credit_high,2) #
        self.taxes_low = round(((self.return_pre_tax_low-self.invest_low-self.low_fees)*taxes)-tax_credit_low,2) #
        self.taxes_close = round(((self.return_pre_tax_close-self.invest_close-self.close_fees)*taxes)-tax_credit_close,2) #
        if self.taxes_high < 0:
            self.tax_credit_high = self.taxes_high*-1
            self.taxes_high = 0
        if self.taxes_low < 0:
            self.tax_credit_low = self.taxes_low*-1
            self.taxes_low = 0
        if self.taxes_close < 0:
            self.tax_credit_close = self.taxes_close*-1
            self.taxes_close = 0
        self.return_minus_taxes_high = round(self.return_pre_tax_high - self.taxes_high,2)
        self.return_minus_taxes_low = round(self.return_pre_tax_low - self.taxes_low,2)
        self.return_minus_taxes_close = round(self.return_pre_tax_close - self.taxes_close,2)
        return self.tax_credit_high, self.tax_credit_low, self.tax_credit_close

    def add_unused(self):
        self.return_final_high = round(self.return_minus_taxes_high + self.unused_high,2)
        self.return_final_low = round(self.return_minus_taxes_low + self.unused_low,2)
        self.return_final_close = round(self.return_minus_taxes_close + self.unused_close,2)
        return self.return_final_high, self.return_final_low, self.return_final_close

def backtesting(timeframe, package, amount_high, amount_low, amount_close, tax_credit_high, tax_credit_low, tax_credit_close, safety_margin):
    amount_high = amount_high
    amount_low = amount_low
    tax_credit_high = tax_credit_high
    tax_credit_low = tax_credit_low
    backtest_breakdown = []
    for trade in package:
        trade_backtest = Backtest(trade["buy_date"],trade["sell_date"], trade["name"], trade["ticker"], timeframe, 
        trade["trade"].buy_high, trade["trade"].buy_low, trade["trade"].buy_close, trade["trade"].sell_high, trade["trade"].sell_low, trade["trade"].sell_close, 
        trade["dividend_amount"], amount_high, amount_low, amount_close)
        # buy_date, sell_date, name,  ticker, timeframe, buy_high, buy_low, sell_high, sell_low, dividend, amount_high, amount_low
        trade_backtest.buy_stocks()
        trade_backtest.substract_fees("buy")
        trade_backtest.calculate_unused()
        trade_backtest.sell_stocks(safety_margin)
        trade_backtest.substract_fees("sell")
        trade_backtest.add_dividend()
        tax_credit_high, tax_credit_low, tax_credit_close = trade_backtest.calculate_taxes(tax_credit_high, tax_credit_low, tax_credit_close)
        amount_high, amount_low, amount_close = trade_backtest.add_unused()
        backtest_breakdown.append(trade_backtest)
    last_date = package[-1]["sell_date"]
    return last_date, amount_high, amount_low, amount_close, tax_credit_high, tax_credit_low, tax_credit_close, backtest_breakdown