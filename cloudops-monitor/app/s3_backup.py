import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class S3BackupClient:
    """S3 backup utility that relies on EC2 IAM role credentials.

    No access keys are read from configuration. On EC2, boto3 automatically
    resolves temporary credentials from the instance metadata service.
    """

    def __init__(self, bucket_name: str, prefix: str = "cloudops-monitor") -> None:
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self.client = boto3.client("s3")

    def upload_logs(self, log_path: str | Path) -> str:
        path = Path(log_path)
        key = self._key("logs", path.name)
        self._upload_file(path, key)
        return key

    def upload_incident_report(self, incidents: list[dict[str, Any]]) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = self._key("incident-reports", f"incidents-{timestamp}.json")
        body = json.dumps({"generated_at": timestamp, "incidents": incidents}, indent=2, default=str)
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        return key

    def _upload_file(self, path: Path, key: str) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {path}")

        try:
            self.client.upload_file(str(path), self.bucket_name, key, ExtraArgs={"ServerSideEncryption": "AES256"})
        except (BotoCoreError, ClientError):
            logger.exception("Failed to upload %s to s3://%s/%s", path, self.bucket_name, key)
            raise

    def _key(self, category: str, filename: str) -> str:
        return f"{self.prefix}/{category}/{filename}"
