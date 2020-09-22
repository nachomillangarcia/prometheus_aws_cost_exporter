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
client = boto3.client('ce')

if os.environ.get('METRIC_TODAY_DAILY_COSTS') is not None:
    g_cost = Gauge('aws_today_daily_costs', 'Today daily costs from AWS', ['usage_type'])
if os.environ.get('METRIC_YESTERDAY_DAILY_COSTS') is not None:
    g_yesterday = Gauge('aws_yesterday_daily_costs', 'Yesterday daily costs from AWS', ['usage_type'])
if os.environ.get('METRIC_TODAY_DAILY_USAGE') is not None:
    g_usage = Gauge('aws_today_daily_usage', 'Today daily usage from AWS', ['usage_type', 'unit'])
if os.environ.get('METRIC_TODAY_DAILY_USAGE_NORM') is not None:
    g_usage_norm = Gauge('aws_today_daily_usage_norm', 'Today daily usage normalized from AWS', ['usage_type'])

scheduler = BackgroundScheduler()

def aws_query():
    print("Calculating costs...")
    now = datetime.now()
    yesterday = datetime.today() - timedelta(days=1)
    two_days_ago = datetime.today() - timedelta(days=2)
    if os.environ.get('METRIC_TODAY_DAILY_COSTS') is not None:

        r = client.get_cost_and_usage(
            TimePeriod={
                'Start': yesterday.strftime("%Y-%m-%d"),
                'End':  now.strftime("%Y-%m-%d")
            },
            Granularity="DAILY",
            Metrics=["BlendedCost"],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }
            ]
        )
        cost_groups = r["ResultsByTime"][0]["Groups"]
        for cost_group in cost_groups:
            label = cost_group["Keys"][0]
            cost = cost_group["Metrics"]["BlendedCost"]["Amount"]
            g_cost.labels(usage_type=label).set(float(cost))
            print("Updated AWS Daily costs for %s to: %s" %(label, cost))

    if os.environ.get('METRIC_YESTERDAY_DAILY_COSTS') is not None:
        r = client.get_cost_and_usage(
            TimePeriod={
                'Start': two_days_ago.strftime("%Y-%m-%d"),
                'End':  yesterday.strftime("%Y-%m-%d")
            },
            Granularity="DAILY",
            Metrics=["BlendedCost"],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }
            ]
        )
        cost_groups = r["ResultsByTime"][0]["Groups"]
        for cost_group in cost_groups:
            label = cost_group["Keys"][0]
            cost = cost_group["Metrics"]["BlendedCost"]["Amount"]
            g_yesterday.labels(usage_type=label).set(float(cost))
            print("Yesterday's AWS Daily costs for %s to: %s" %(label, cost))


    if os.environ.get('METRIC_TODAY_DAILY_USAGE') is not None:
        r = client.get_cost_and_usage(
            TimePeriod={
                'Start': yesterday.strftime("%Y-%m-%d"),
                'End':  now.strftime("%Y-%m-%d")
            },
            Granularity="DAILY",
            Metrics=["UsageQuantity"],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }
            ]
        )

        usage_groups = r["ResultsByTime"][0]["Groups"]
        for usage_group in usage_groups:
            label = usage_group["Keys"][0]
            usage = usage_group["Metrics"]["UsageQuantity"]["Amount"]
            unit = usage_group["Metrics"]["UsageQuantity"]["Unit"]
            g_usage.labels(usage_type=label, unit=unit).set(float(usage))
            print("Updated AWS Daily Usage for %s to: %s %s" %(label, usage, unit))

    if os.environ.get('METRIC_TODAY_DAILY_USAGE_NORM') is not None:

        r = client.get_cost_and_usage(
            TimePeriod={
                'Start': yesterday.strftime("%Y-%m-%d"),
                'End':  now.strftime("%Y-%m-%d")
            },
            Granularity="DAILY",
            Metrics=["NormalizedUsageAmount"],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }
            ]
        )

        usage_groups = r["ResultsByTime"][0]["Groups"]
        for usage_group in usage_groups:
            label = usage_group["Keys"][0]
            usage = usage_group["Metrics"]["NormalizedUsageAmount"]["Amount"]
            g_usage_norm.labels(usage_type=label).set(float(usage))
            print("Updated AWS Daily Usage for %s to: %s" %(label, usage))

    print("Finished calculating costs")

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
