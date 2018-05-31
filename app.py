from flask import Flask,Response
from prometheus_client import Gauge,generate_latest
import boto3
from datetime import datetime, timedelta
import time, os
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

QUERY_PERIOD = os.getenv('QUERY_PERIOD', "1800")

app = Flask(__name__)
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
g = Gauge('aws_today_daily_costs', 'Today daily costs from AWS')
client = boto3.client('ce')

scheduler = BackgroundScheduler()

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
    cost = r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"]
    print("Updated AWS Daily costs: %s" %(cost))
    return float(r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"])


@app.route('/metrics/')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health():
    return "OK"

scheduler.start()
scheduler.add_job(
    func=aws_query,
    trigger=IntervalTrigger(seconds=int(QUERY_PERIOD),start_date=(datetime.now() + timedelta(seconds=1))),
    id='aws_query',
    name='Run AWS Query',
    replace_existing=True
    )
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
