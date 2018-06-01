# PROMETHEUS AWS DAILY COST EXPORTER

[![](https://dockerbuildbadges.quelltext.eu/status.svg?organization=nachomillangarcia&repository=prometheus_aws_cost_exporter)](https://hub.docker.com/r/nachomillangarcia/prometheus_aws_cost_exporter/builds/)


## INTRO
Are you looking for some system that alerts when your today's spending on AWS exceeds some limit?  That's just what this exporter has made for.

CloudWatch doesn't allow you to track costs in the same day, just past days or monthly predictions.

The exporter is a Python server that connects to AWS Cost Explorer with a customizable period, and exposes last responses as Prometheus metrics.
