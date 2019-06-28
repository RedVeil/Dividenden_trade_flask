import os
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from flask import Flask, render_template, Blueprint, redirect, request, jsonify, send_from_directory, Response, send_file, Markup
from analysis import build_packages_alternative as package

bp = Blueprint('flask_pages', __name__)

class Strategy():
    def __init__(self, graph_hist):
        self.graph_hist = graph_hist


  
@bp.route('/test', methods=("GET","POST"))
def chart():
    graph_hist_2008 = strategy.graph_hist[2008]
    line_labels = range(len(graph_hist_2008))
    line_values = graph_hist_2008
    return render_template('test.html', max=10000, labels=line_labels, values=line_values)
