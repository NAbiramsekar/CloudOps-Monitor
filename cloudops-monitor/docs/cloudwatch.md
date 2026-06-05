# CloudWatch Agent Guide

## Install Agent

```bash
sudo apt-get update
sudo apt-get install -y amazon-cloudwatch-agent
```

Ensure the EC2 instance profile includes `CloudWatchAgentServerPolicy`.

## Configure Metrics

Create `/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`:

```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 60,
        "totalcpu": true
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      }
    }
  }
}
```

Start the agent:

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s
```

## Monitor EC2 CPU

Use the default `AWS/EC2` namespace for CPU utilization. Create an alarm when average CPU exceeds your threshold, for example 80% for 5 minutes.

## Monitor Memory

Memory metrics are published by the CloudWatch Agent under the `CWAgent` namespace as `mem_used_percent`. Alarm on sustained memory usage above 85%.

## Monitor Disk Usage

Disk metrics are published under `CWAgent` as `disk_used_percent`. Alarm when root volume usage exceeds 80% so log growth or Prometheus storage pressure is caught early.
