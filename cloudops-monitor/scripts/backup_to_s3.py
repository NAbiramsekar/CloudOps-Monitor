#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from app.s3_backup import S3BackupClient
from app.store import incident_store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload CloudOps Monitor backups to S3 using IAM role auth.")
    parser.add_argument("--bucket", default=os.getenv("S3_BACKUP_BUCKET"), help="S3 bucket name.")
    parser.add_argument("--prefix", default=os.getenv("S3_BACKUP_PREFIX", "cloudops-monitor"), help="S3 key prefix.")
    parser.add_argument("--log-file", default="/var/log/cloudops-monitor/app.log", help="Application log file path.")
    parser.add_argument("--include-incidents", action="store_true", help="Upload a JSON incident report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.bucket:
        raise SystemExit("S3 bucket is required. Set S3_BACKUP_BUCKET or pass --bucket.")

    backup = S3BackupClient(bucket_name=args.bucket, prefix=args.prefix)

    log_path = Path(args.log_file)
    if log_path.exists():
        key = backup.upload_logs(log_path)
        print(f"Uploaded logs to s3://{args.bucket}/{key}")
    else:
        print(f"Skipped missing log file: {log_path}")

    if args.include_incidents:
        incidents = [incident.model_dump(mode="json") for incident in incident_store.list()]
        key = backup.upload_incident_report(incidents)
        print(f"Uploaded incident report to s3://{args.bucket}/{key}")


if __name__ == "__main__":
    main()
