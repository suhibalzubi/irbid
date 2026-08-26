#!/usr/bin/env bash
# Backup script for PostgreSQL database (simple)
# Usage: ./scripts/backup_db.sh /path/to/output_dir

set -e
OUT_DIR=${1:-./backups}
mkdir -p "$OUT_DIR"
TIMESTAMP=$(date +"%Y%m%dT%H%M%S")
FILENAME="irbid_db_$TIMESTAMP.sql.gz"

# Environment variables required: PGPASSWORD, PGHOST, PGUSER, PGDATABASE, PGPORT
: ${PGHOST:=localhost}
: ${PGPORT:=5432}
: ${PGUSER:=irbid}
: ${PGDATABASE:=irbid_db}

echo "Backing up database $PGDATABASE at $PGHOST:$PGPORT"
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" | gzip > "$OUT_DIR/$FILENAME"

echo "Backup saved to $OUT_DIR/$FILENAME"

# Optional: upload to S3 if AWS env vars are set (AWS_BUCKET)
if [ ! -z "$AWS_BUCKET" ]; then
  if command -v aws >/dev/null 2>&1; then
    echo "Uploading to S3://$AWS_BUCKET/"
    aws s3 cp "$OUT_DIR/$FILENAME" "s3://$AWS_BUCKET/" --acl private
    echo "Upload complete"
  else
    echo "AWS CLI not found; skipping S3 upload"
  fi
fi
