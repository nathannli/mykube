#!/bin/bash

# Configurable Variables
NAMESPACE="postgres"
POD_NAME="my-release-postgresql-0"
DB_NAME="finance"
DB_USER="db username"
DB_PASSWORD="db password"
BACKUP_DIR="/home/nathan/pg-backup"
BACKUP_FILE="backup_$(date +\%Y\%m\%d_%H%M).sql"
REMOTE_DIR="/nathan/pg-backup"
FTP_HOST="195.168.1.96"
FTP_USER="ftp username"
FTP_PASS="ftp pass"
KEEP_DAYS=60  # Number of days to keep local backups

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# stream pg_dump directly to local file
kubectl exec -n postgres my-release-postgresql-0 -- \
    sh -c "PGPASSWORD='$DB_PASSWORD' pg_dump -U '$DB_USER' -F p -b -v '$DB_NAME'" > "$BACKUP_DIR/$BACKUP_FILE"

# Verify the backup was copied successfully
if [[ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]]; then
    echo "Backup failed: File not found!" >&2
    exit 1
fi

# Upload backup file to FTP server
echo "Uploading $BACKUP_FILE to FTP server..."
curl -T "$BACKUP_DIR/$BACKUP_FILE" ftp://$FTP_USER:$FTP_PASS@$FTP_HOST$REMOTE_DIR/ --silent --show-error

# Check if upload was successful
if [[ $? -eq 0 ]]; then
    echo "Backup successfully uploaded to FTP."
else
    echo "FTP upload failed!" >&2
    exit 1
fi

# Find old backups to delete
echo "Checking for old backups to delete..."
find "$BACKUP_DIR" -type f -name "backup_*.sql" -mtime +$KEEP_DAYS | while read backup_path; do
    echo "Deleting $backup_path"
    backup_file=$(basename "$backup_path")
    
    # Delete from local storage
    echo "Deleting $backup_file locally..."
    rm "$backup_path"
    
    # Delete from FTP server
    echo "Deleting $backup_file from FTP server..."
    curl -u "$FTP_USER:$FTP_PASS" -Q "DELE $REMOTE_DIR/$backup_file" ftp://$FTP_HOST --silent
    
    if [[ $? -eq 0 ]]; then
        echo "Successfully deleted $backup_file from FTP server."
    else
        echo "Warning: Failed to delete $backup_file from FTP server." >&2
    fi
done

# Check if any backups were deleted
if [[ $? -ne 0 ]]; then
    echo "No old backups found to delete."
fi


echo "Backup process completed successfully."
