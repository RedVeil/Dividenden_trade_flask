import os
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from flask import Flask, render_template, redirect, request
import web_build_packages as package
import web_filter_companies as filter_companies

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
    average_high_threshold = IntegerField(
        "Threshold Hoher Durchschnitt", default=10)
    average_high_strikes = IntegerField("Strikes", default=1)
    average_medium_threshold = IntegerField(
        "Threshold Mittlerer Durchschnitt", default=5)
    average_medium_strikes = IntegerField("Strikes", default=1)
    average_low_threshold = IntegerField(
        "Threshold Niedriger Durchschnitt", default=2)
    average_low_strikes = IntegerField("Strikes", default=1)
    median_high_threshold = IntegerField("Threshold Hoher Median", default=10)
    median_high_strikes = IntegerField("Strikes", default=1)
    median_medium_threshold = IntegerField(
        "Threshold Durschnitts Median", default=5)
    median_medium_strikes = IntegerField("Strikes", default=1)
    median_low_threshold = IntegerField(
        "Threshold Niedriger Median", default=1)
    median_low_strikes = IntegerField("Strikes", default=1)
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

@app.route('/', methods=("GET", "POST"))
def full_controll():
    form = ExpertForm()
    if request.method == "POST":
        form_data = form.data
        high_hists, medium_hists, low_hists, package_objects, breakdowns_per_year = filter_companies.webcall(
            form_data)
        total_values_high = []
        total_values_medium = []
        total_values_low = []
        total_trades = []
        total_buy_dates = []
        total_breakdowns = []
        for key in low_hists.keys():
            for i in low_hists[key]:
                total_values_low.append(i)
            for n in high_hists[key]:
                total_values_high.append(n)
            for x in medium_hists[key]:
                total_values_medium.append(x)
        for key in package_objects.keys():
            for trade in package_objects[key].trades:
                total_trades.append([trade[0], trade[1],trade[2],round(trade[3],2),round(trade[4],2),round(trade[5],2),round(trade[6],2), trade[7]])
                total_buy_dates.append(trade[0])
        for key in breakdowns_per_year.keys():
            for k in breakdowns_per_year[key]:
                total_breakdowns.append(breakdowns_per_year[key][k])
        line_labels = total_buy_dates
        return render_template('results.html', labels=line_labels, values_high=total_values_high,
        values_medium=total_values_medium, values_low=total_values_low ,
        trades=total_trades, breakdowns=total_breakdowns, timeframe_buy = form_data["timeframe_buy"], timeframe_sell= form_data["timeframe_sell"])
    return render_template("landing.html", form=form)
