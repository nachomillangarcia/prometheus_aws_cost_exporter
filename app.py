from flask import Flask,Response
from prometheus_client import Gauge,generate_latest
import boto3
from datetime import datetime, timedelta

app = Flask(__name__)
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
g = Gauge('today_daily_costs', 'Today daily costs from AWS')
client = boto3.client('ce')

def aws_query():
    now = datetime.now()
    yesterday = datetime.today() - timedelta(days=1)
    r = client.get_cost_and_usage(
        TimePeriod={
            'Start': yesterday.strftime("%Y-%m-%d"),
            'End':  now.strftime("%Y-%m-%d")
        },
        Granularity="DAILY",
        Metrics=["BlendedCost"]
    )
    return float(r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"])


@app.route('/metrics/')
def metrics():
    g.set(aws_query())
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health():
    return "OK"
