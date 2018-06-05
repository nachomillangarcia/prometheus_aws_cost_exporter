# Prometheus AWS Daily Cost Exporter

[![](https://dockerbuildbadges.quelltext.eu/status.svg?organization=nachomillangarcia&repository=prometheus_aws_cost_exporter)](https://hub.docker.com/r/nachomillangarcia/prometheus_aws_cost_exporter/builds/)


## Intro
Are you looking for some system that alerts when your today's spending on AWS exceeds some limit?  That's just what this exporter is made for.

CloudWatch doesn't allow you to track costs in the same day, just past days or monthly predictions.

The exporter is a Python server that connects to AWS Cost Explorer with a customizable period, and exposes last responses as Prometheus metrics.

## Configuration
Configuration is made through environment variables:

| Environment variable        | Description           | Default  |
| ------------- |:-------------:| -----:|
| QUERY_PERIOD      | Period to update metrics, querying AWS Cost Explorer API (0.01$ per request) | 1800 |
| METRIC_TODAY_DAILY_COSTS      | Enable aws_today_daily_costs metric      |   Not set |
| METRIC_YESTERDAY_DAILY_COSTS | Enable aws_yesterday_daily_costs metric      |   Not set |
| METRIC_TODAY_DAILY_USAGE | Enable aws_today_daily_usage metric      |   Not set |
| METRIC_TODAY_DAILY_USAGE_NORM | Enable aws_today_daily_usage_norm metric      |   Not set |
