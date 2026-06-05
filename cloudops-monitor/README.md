# CloudOps Monitor - Cloud Monitoring & Incident Response Platform

CloudOps Monitor is a production-style DevOps demo project that combines a FastAPI backend, vanilla JavaScript dashboard, incident management APIs, Prometheus metrics, Grafana dashboards, Nginx reverse proxying, Docker Compose orchestration, AWS deployment guidance, S3 backups, CloudWatch monitoring, and GitHub Actions CI/CD.

## Architecture Diagram

```text
GitHub
  |
  v
GitHub Actions
  |
  v
Docker Build
  |
  v
EC2 Deployment
  |
  v
Nginx :80
  |
  v
FastAPI :8000 ---- /metrics ----> Prometheus :9090 ----> Grafana :3000
  |
  v
S3 backups for logs and incident reports

CloudWatch Agent monitors EC2 CPU, memory, and disk usage.
```

## Project Structure

```text
cloudops-monitor/
  app/                         FastAPI app, incident models, metrics, S3 backup client
  frontend/                    HTML, CSS, and vanilla JavaScript dashboard
  nginx/default.conf           Reverse proxy from port 80 to FastAPI
  prometheus/prometheus.yml    Prometheus scrape config
  grafana/                     Provisioned datasource and dashboard
  scripts/backup_to_s3.py      IAM-role based S3 backup utility
  tests/                       FastAPI endpoint tests
  docs/                        AWS EC2, S3, IAM, and CloudWatch guides
  .github/workflows/deploy.yml GitHub Actions CI/CD pipeline
  Dockerfile                   Python 3.12 FastAPI image
  docker-compose.yml           FastAPI, Nginx, Prometheus, Grafana stack
```

## Local Setup

```bash
cd cloudops-monitor
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open:

- Dashboard: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`
- API docs: `http://localhost:8000/docs`

## Docker Commands

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs -f fastapi
docker compose down
```

Service URLs:

- Application through Nginx: `http://localhost`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Health check for load balancers and monitors |
| GET | `/metrics` | Prometheus metrics |
| GET | `/dashboard/summary` | Dashboard status summary |
| GET | `/incidents` | List incidents |
| POST | `/incidents` | Create incident |
| PUT | `/incidents/{id}` | Update incident |
| DELETE | `/incidents/{id}` | Delete incident |

## Monitoring Architecture

FastAPI exposes Prometheus metrics through `/metrics`:

- `cloudops_http_requests_total`
- `cloudops_http_request_duration_seconds`
- `cloudops_http_errors_total`
- `cloudops_application_uptime_seconds`

Prometheus scrapes the FastAPI service every 15 seconds. Grafana is automatically provisioned with a Prometheus datasource and a dashboard showing requests per minute, error count, application uptime, and response time.

## AWS Deployment Steps

1. Launch an Ubuntu EC2 instance.
2. Attach an IAM role with CloudWatch Agent permissions and S3 write access scoped to the backup bucket.
3. Configure security groups for SSH, Nginx port 80, and restricted Grafana/Prometheus access.
4. Install Docker and the Docker Compose plugin.
5. Clone the repository into `/opt/cloudops-monitor`.
6. Copy `.env.example` to `.env` and set S3/Grafana values.
7. Run `docker compose up -d --build`.
8. Configure CloudWatch Agent for CPU, memory, and disk metrics.

Detailed guides:

- [AWS Deployment](docs/aws-deployment.md)
- [CloudWatch Agent](docs/cloudwatch.md)

## S3 Backups

The backup utility never uses AWS access keys. It relies on the EC2 IAM role through boto3 default credential resolution.

```bash
S3_BACKUP_BUCKET=your-bucket python scripts/backup_to_s3.py \
  --log-file /var/log/cloudops-monitor/app.log \
  --include-incidents
```

## CI/CD Flow

The GitHub Actions workflow performs:

1. Checkout Code
2. Setup Python
3. Install Dependencies
4. Run Tests
5. Build Docker Image
6. Validate Docker Compose
7. Deploy to EC2 via SSH on pushes to `main`

Required repository secrets:

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_PRIVATE_KEY`

## Troubleshooting

Check container status:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs -f fastapi
```

Validate Prometheus scraping:

```bash
curl http://localhost:9090/api/v1/targets
```

Validate health through Nginx:

```bash
curl http://localhost/health
```

If Grafana has no data, confirm Prometheus has an `UP` target for `cloudops-fastapi`, then refresh the dashboard time range.

## Files Created

- `app/main.py`: FastAPI app, static dashboard serving, health endpoint, incident APIs, dashboard summary, and Prometheus metrics endpoint.
- `app/models.py`: Pydantic incident schemas and enums.
- `app/store.py`: Thread-safe in-memory incident store.
- `app/metrics.py`: Prometheus counters, histograms, and uptime gauge.
- `app/s3_backup.py`: IAM-role based S3 backup client.
- `frontend/index.html`: Responsive dashboard and incident management UI.
- `frontend/styles.css`: Professional responsive styling.
- `frontend/app.js`: Dashboard polling and incident CRUD interactions.
- `Dockerfile`: Python 3.12 FastAPI container image.
- `docker-compose.yml`: FastAPI, Nginx, Prometheus, and Grafana services on one Docker network.
- `nginx/default.conf`: Reverse proxy routing user traffic to FastAPI.
- `prometheus/prometheus.yml`: 15-second scrape configuration for FastAPI metrics.
- `grafana/provisioning/*`: Automatic Prometheus datasource and dashboard provisioning.
- `grafana/dashboards/cloudops-monitor.json`: Grafana panels for RPM, errors, uptime, and latency.
- `scripts/backup_to_s3.py`: CLI utility for S3 log and incident backups.
- `.github/workflows/deploy.yml`: GitHub Actions CI/CD pipeline.
- `docs/aws-deployment.md`: EC2, security group, Docker, IAM role, and S3 deployment guide.
- `docs/cloudwatch.md`: CloudWatch Agent setup for CPU, memory, and disk monitoring.
- `tests/test_api.py`: API lifecycle and metrics tests.
