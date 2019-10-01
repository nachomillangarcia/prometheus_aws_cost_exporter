from flask import Flask,Response
from prometheus_client import Gauge,generate_latest
import boto3
from datetime import datetime, timedelta
import time, os
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import yaml
import json
import glob

QUERY_PERIOD = os.getenv('QUERY_PERIOD', "1800")
CONFIG_PATH = os.getenv('CONFIG_PATH', "/cost-exporter")

app = Flask(__name__)
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
client = boto3.client('ce')

if os.environ.get('METRIC_TODAY_DAILY_COSTS') is not None:
    g_cost = Gauge('aws_today_daily_costs', 'Today daily costs from AWS', ["tag"])
if os.environ.get('METRIC_YESTERDAY_DAILY_COSTS') is not None:
    g_yesterday = Gauge('aws_yesterday_daily_costs', 'Yesterday daily costs from AWS', ["tag"])
if os.environ.get('METRIC_TODAY_DAILY_USAGE') is not None:
    g_usage = Gauge('aws_today_daily_usage', 'Today daily usage from AWS', ["tag"])
if os.environ.get('METRIC_TODAY_DAILY_USAGE_NORM') is not None:
    g_usage_norm = Gauge('aws_today_daily_usage_norm', 'Today daily usage normalized from AWS', ["tag"])

if os.environ.get('AWS_FILTER') is not None:
    path = CONFIG_PATH
    filter_list = list()
    for filename in glob.glob(os.path.join(path, '*.yaml')):
        print(filename)
        with open(filename, 'r') as stream:
            try:
                filter_list.append(yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                print(exc)

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
            Metrics=["BlendedCost"]
        )
        cost = r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"]
        print("Updated AWS Daily costs: %s" %(cost))
        g_cost.labels(tag="").set(float(cost))

    if os.environ.get('METRIC_YESTERDAY_DAILY_COSTS') is not None:
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
        g_yesterday.labels(tag="").set(float(cost_yesterday))


    if os.environ.get('METRIC_TODAY_DAILY_USAGE') is not None:
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
        g_usage.labels(tag="").set(float(usage))

    if os.environ.get('METRIC_TODAY_DAILY_USAGE_NORM') is not None:

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
        g_usage_norm.labels(tag="").set(float(usage_norm))

    if os.environ.get('AWS_FILTER') is not None:
        aws_query_with_filter()

    print("Finished calculating costs")

    return 0

def aws_query_with_filter():
    now = datetime.now()
    yesterday = datetime.today() - timedelta(days=1)
    two_days_ago = datetime.today() - timedelta(days=2)

    for filter in filter_list:
        filter_string = format_filter(filter)
        filter_json = json.loads(filter_string)

        taglist = list()
        for k, v in filter['filter']['tags'].items():
            taglist.append(k+"="+str(v))
        taglist.sort()
        tags = ','.join(taglist)

        if os.environ.get('METRIC_TODAY_DAILY_COSTS') is not None:

            r = client.get_cost_and_usage(
                TimePeriod={
                    'Start': yesterday.strftime("%Y-%m-%d"),
                    'End':  now.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["BlendedCost"],
                Filter=filter_json
            )
            cost = r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"]
            print("Updated AWS Daily costs: %s" %(cost))
            g_cost.labels(tag=tags).set(float(cost))

        if os.environ.get('METRIC_YESTERDAY_DAILY_COSTS') is not None:
            r = client.get_cost_and_usage(
                TimePeriod={
                    'Start': two_days_ago.strftime("%Y-%m-%d"),
                    'End':  yesterday.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["BlendedCost"],
                Filter=filter_json
            )
            cost_yesterday = r["ResultsByTime"][0]["Total"]["BlendedCost"]["Amount"]
            print("Yesterday's AWS Daily costs: %s" %(cost_yesterday))
            g_yesterday.labels(tag=tags).set(float(cost_yesterday))


        if os.environ.get('METRIC_TODAY_DAILY_USAGE') is not None:
            r = client.get_cost_and_usage(
                TimePeriod={
                    'Start': yesterday.strftime("%Y-%m-%d"),
                    'End':  now.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["UsageQuantity"],
                Filter=filter_json
            )
            usage = r["ResultsByTime"][0]["Total"]["UsageQuantity"]["Amount"]
            print("Updated AWS Daily Usage: %s" %(usage))
            g_usage.labels(tag=tags).set(float(usage))

        if os.environ.get('METRIC_TODAY_DAILY_USAGE_NORM') is not None:

            r = client.get_cost_and_usage(
                TimePeriod={
                    'Start': yesterday.strftime("%Y-%m-%d"),
                    'End':  now.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["NormalizedUsageAmount"],
                Filter=filter_json
            )
            usage_norm = r["ResultsByTime"][0]["Total"]["NormalizedUsageAmount"]["Amount"]
            print("Updated AWS Daily Usage Norm: %s" %(usage_norm))
            g_usage_norm.labels(tag=tags).set(float(usage_norm))
    return 0

def format_filter(filter):
    tags = ""
    for key in filter['filter']['tags']:
        values_list = str(filter['filter']['tags'][key]).split(",")
        values=""
        for value in values_list:
            if values != "":
                values += ","
            values += '"' + value + '"'
        if tags != "":
            tags += ","
        tags += '{  "Tags": {   "Key": "' + key + '",  "Values": [ ' + values + '    ]  } }'
    if len(filter['filter']['tags']) == 1:
        return tags
    return '{ "And": [' + tags + ']}'

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
