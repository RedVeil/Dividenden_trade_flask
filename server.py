import os
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from flask import Flask, render_template, redirect, request
import v2_companies_and_filter as companies_and_filter
import forecasting 

app = Flask(__name__)
app.config["SECRET_KEY"] = "Secret Key"

@app.route('/test', methods = ["GET","POST"])
def test():
    if request.method == "POST":
        form = request.form
        print(form)
        print(form["test1"])
    return render_template("test.html")


@app.route('/', methods=["GET", "POST"])
def full_controll():
    if request.method == "POST":
        form_data = request.form
        print(form_data)
        backtest_breakdowns = companies_and_filter.webcall(
            form_data)
        graph_high = []
        graph_low = []
        graph_average = []
        total_trades = []
        total_buy_dates = []
        breakdowns = []
        for year in backtest_breakdowns.keys():
            for backtest in backtest_breakdowns[year]:
                high = backtest.return_minus_taxes_high
                low = backtest.return_minus_taxes_low
                graph_high.append(high)
                graph_low.append(low)
                high = high.replace(".", "")
                high = high.replace(",",".")
                low = low.replace(".","")
                low = low.replace(",", ".")
                high = float(high)
                low = float(low)
                average = round((high+low)/2,2)
                graph_average.append(average)
                total_trades.append([backtest.buy_date, backtest.sell_date,backtest.ticker,backtest.name,backtest.buy_high,backtest.buy_low,backtest.sell_high,backtest.sell_low])
                total_buy_dates.append(backtest.buy_date)
                breakdowns.append(backtest)
                max_return = max(high)
                step_size = int(max_return/20)
        return render_template('results.html', labels=total_buy_dates, values_high=graph_high,
        values_medium=graph_average, values_low=graph_low ,
        total_trades=total_trades, breakdowns=breakdowns, timeframe_buy = form_data["timeframe"], step_size=step_size, max_return=max_return)
    return render_template("index.html")

@app.route("/forecast", methods=["GET","POST"])
def forecast():
    form = ForecastForm()
    if request.method == "POST":
        form_data = form.data
        forecast_package = forecasting.webcall(form_data)
        return render_template("forecast_results.html", package=forecast_package)
    return render_template("forecast.html", form=form )