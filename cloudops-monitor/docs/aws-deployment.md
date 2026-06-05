# AWS Deployment Guide

## 1. Launch EC2

1. Open the EC2 console and launch an Ubuntu 24.04 LTS instance.
2. Select an instance size such as `t3.small` for a demo or `t3.medium` for heavier Grafana usage.
3. Attach an IAM role with S3 write permissions for the backup bucket and CloudWatch Agent permissions.
4. Allocate and associate an Elastic IP for stable access.

## 2. Security Groups

Allow only the ports required for the platform:

| Port | Source | Purpose |
| --- | --- | --- |
| 22 | Your IP | SSH deployment |
| 80 | 0.0.0.0/0 | Nginx and dashboard |
| 3000 | Your IP or VPN CIDR | Grafana |
| 9090 | Your IP or VPN CIDR | Prometheus troubleshooting |

Restrict Grafana and Prometheus in production behind VPN, SSO, or private networking.

## 3. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and back in so the `ubuntu` user can run Docker.

## 4. Run Docker Compose

```bash
sudo mkdir -p /opt/cloudops-monitor
sudo chown ubuntu:ubuntu /opt/cloudops-monitor
git clone https://github.com/YOUR_ORG/cloudops-monitor.git /opt/cloudops-monitor
cd /opt/cloudops-monitor
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Open `http://EC2_PUBLIC_IP` for the dashboard and `http://EC2_PUBLIC_IP:3000` for Grafana.

## 5. IAM Role

Create an IAM role for EC2 with these managed policies:

- `CloudWatchAgentServerPolicy`
- A custom S3 policy scoped to the backup bucket

Example S3 policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:AbortMultipartUpload"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/cloudops-monitor/*"
    }
  ]
}
```

Attach the role to the EC2 instance. The application and `scripts/backup_to_s3.py` use boto3 default credential resolution, which reads the IAM role credentials automatically.

## 6. Create S3 Bucket

```bash
aws s3api create-bucket --bucket YOUR_BUCKET_NAME --region us-east-1
aws s3api put-bucket-encryption --bucket YOUR_BUCKET_NAME --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket YOUR_BUCKET_NAME --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

Run a backup:

```bash
S3_BACKUP_BUCKET=YOUR_BUCKET_NAME python scripts/backup_to_s3.py --log-file /var/log/cloudops-monitor/app.log --include-incidents
```
