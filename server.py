import os
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from flask import Flask, render_template, redirect, request
import v2_companies_and_filter as companies_and_filter
import forecasting 

app = Flask(__name__)
app.config["SECRET_KEY"] = "Secret Key"

@app.route('/test')
def test():
    return render_template("test.html")

class ExpertForm(FlaskForm):
    timeframe_buy = IntegerField("Kaufzeitraum", default=60)
    timeframe_sell = IntegerField("Verkaufszeitraum", default=10)
    start_year = IntegerField("Start Jahr", default=2008)
    end_year = IntegerField("End Jahr", default=2018)
    start_amount = IntegerField("Start Kapital", default=1000)
    average_threshold = IntegerField(
        "Threshold Hoher Durchschnitt", default=10)
    average_strikes = IntegerField("Strikes", default=1)
    median_threshold = IntegerField("Threshold Hoher Median", default=10)
    median_strikes = IntegerField("Strikes", default=1)
    bad_trades_threshold = IntegerField(
        "Threshold Negativer Trades", default=10)
    bad_trades_strikes = IntegerField("Strikes", default=2)
    bad_trades2_threshold = IntegerField(
        "Threshold2 Negativer Trades", default=20)
    bad_trades2_strikes = IntegerField("Strikes", default=4)
    severe_trades_threshold = IntegerField(
        "Threshold Trades unter -10%", default=10)
    severe_trades_strikes = IntegerField("Strikes", default=4)
    great_trades_threshold = IntegerField(
        "Threshold Trades ueber 10%", default=6)
    great_trades_strikes = IntegerField("Strikes", default=1)
    averages_multiplier = IntegerField("Multiplier Durschnitt", default=100)
    medians_multiplier = IntegerField("Multiplier Median", default=100)
    bad_trades_multiplier = IntegerField(
        "Multiplier Negative Trades", default=100)
    severe_trades_multiplier = IntegerField(
        "Multiplier Trades unter -10%", default=100)
    great_trades_multiplier = IntegerField(
        "Multiplier Trades ueber 10%", default=100)
    submit = SubmitField()

@app.route('/', methods=["GET", "POST"])
def full_controll():
    form = ExpertForm()
    if request.method == "POST":
        form_data = form.data
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
                average = round((high+low)/2,2)
                graph_high.append(high)
                graph_low.append(low)
                graph_average.append(average)
                total_trades.append([backtest.buy_date, backtest.sell_date,backtest.ticker,backtest.name,backtest.buy_high,backtest.buy_low,backtest.sell_high,backtest.sell_low])
                total_buy_dates.append(backtest.buy_date)
                breakdowns.append(backtest)
        return render_template('results.html', labels=total_buy_dates, values_high=graph_high,
        values_medium=graph_average, values_low=graph_low ,
        total_trades=total_trades, breakdowns=breakdowns, timeframe_buy = form_data["timeframe_buy"], timeframe_sell= form_data["timeframe_sell"])
    return render_template("landing.html", form=form)

class ForecastForm(FlaskForm):
    timeframe_buy = IntegerField("Kaufzeitraum", default=60)
    timeframe_sell = IntegerField("Verkaufszeitraum", default=10)
    start_date = StringField("Start Termin", default="2019-07-20")
    average_threshold = IntegerField(
        "Threshold Hoher Durchschnitt", default=10)
    average_strikes = IntegerField("Strikes", default=1)
    median_threshold = IntegerField("Threshold Hoher Median", default=10)
    median_strikes = IntegerField("Strikes", default=1)
    bad_trades_threshold = IntegerField(
        "Threshold Negativer Trades", default=10)
    bad_trades_strikes = IntegerField("Strikes", default=2)
    bad_trades2_threshold = IntegerField(
        "Threshold2 Negativer Trades", default=20)
    bad_trades2_strikes = IntegerField("Strikes", default=4)
    severe_trades_threshold = IntegerField(
        "Threshold Trades unter -10%", default=10)
    severe_trades_strikes = IntegerField("Strikes", default=4)
    great_trades_threshold = IntegerField(
        "Threshold Trades ueber 10%", default=6)
    great_trades_strikes = IntegerField("Strikes", default=1)
    averages_multiplier = IntegerField("Multiplier Durschnitt", default=100)
    medians_multiplier = IntegerField("Multiplier Median", default=100)
    bad_trades_multiplier = IntegerField(
        "Multiplier Negative Trades", default=100)
    severe_trades_multiplier = IntegerField(
        "Multiplier Trades unter -10%", default=100)
    great_trades_multiplier = IntegerField(
        "Multiplier Trades ueber 10%", default=100)
    submit = SubmitField()


@app.route("/forecast", methods=["GET","POST"])
def forecast():
    form = ForecastForm()
    if request.method == "POST":
        form_data = form.data
        forecast_package = forecasting.webcall(form_data)
        return render_template("forecast_results.html", package=forecast_package)
    return render_template("forecast.html", form=form )