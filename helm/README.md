# PROMETHEUS AWS DAILY COST EXPLORER

Chart to deploy [prometheus_aws_cost_exporter](https://github.com/nachomillangarcia/prometheus_aws_cost_exporter) on Kubernetes


## Installing the Chart
```
helm install -e METRIC_TODAY_DAILY_COSTS=yes  --name prometheus-aws-cost-exporter --namespace kube-system .
```

## Configuration

The following table lists the configurable parameters of the heptio-ark chart and their default values.

| Parameter | Description | Required | Default |
| --------- | ----------- | ------- | ------- |
| `image` | image and tag to deploy | yes | nachomillangarcia/fluentd-k8s |
| `args` | Arguments for the container | no | [--host, 0.0.0.0]|
| `svcAnnotations` | Annotations for service | no | See values.yaml |
| `podAnnotations` |  Annotations for pod | yes | cluster-admins |
| `env` | Env variables for container | no | See values.yaml |
