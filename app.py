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
g_cost = Gauge('aws_today_daily_costs', 'Today daily costs from AWS')
g_yesterday = Gauge('aws_yesterday_daily_costs', 'Yesterday daily costs from AWS')
g_usage = Gauge('aws_today_daily_usage', 'Today daily usage from AWS')
g_usage_norm = Gauge('aws_today_daily_usage_norm', 'Today daily usage normalized from AWS')
client = boto3.client('ce')

scheduler = BackgroundScheduler()

def aws_query():
    print("Calculating costs...")
    now = datetime.now()
    yesterday = datetime.today() - timedelta(days=1)
    two_days_ago = datetime.today() - timedelta(days=2)
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
    g_cost.set(float(cost))

    r = client.get_cost_and_usage(
        TimePeriod={
            'Start': two_days_ago.strftime("%Y-%m-%d"),
            'End':  yesterday.strftime("%Y-%m-%d")
        },
        Granularity="DAILY",
        Metrics=["BlendedCost"]
    )
    cost_yesterday = r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"]
    print("Yesterday's AWS Daily costs: %s" %(cost_yesterday))
    g_yesterday.set(float(cost_yesterday))


    r = client.get_cost_and_usage(
        TimePeriod={
            'Start': yesterday.strftime("%Y-%m-%d"),
            'End':  now.strftime("%Y-%m-%d")
        },
        Granularity="DAILY",
        Metrics=["UsageQuantity"]
    )
    usage = r["ResultsByTime"][0]["Total"]["UsageQuantity"]["Amount"]
    print("Updated AWS Daily Usage: %s" %(usage))
    g_usage.set(float(usage))

    r = client.get_cost_and_usage(
        TimePeriod={
            'Start': yesterday.strftime("%Y-%m-%d"),
            'End':  now.strftime("%Y-%m-%d")
        },
        Granularity="DAILY",
        Metrics=["NormalizedUsageAmount"]
    )
    usage_norm = r["ResultsByTime"][0]["Total"]["NormalizedUsageAmount"]["Amount"]
    print("Updated AWS Daily Usage Norm: %s" %(usage_norm))
    g_usage_norm.set(float(usage_norm))
    return 0


@app.route('/metrics/')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health():
    return "OK"

scheduler.start()
scheduler.add_job(
    func=aws_query,
    trigger=IntervalTrigger(seconds=int(QUERY_PERIOD),start_date=(datetime.now() + timedelta(seconds=5))),
    id='aws_query',
    name='Run AWS Query',
    replace_existing=True
    )
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
