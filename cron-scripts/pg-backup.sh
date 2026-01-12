#!/bin/bash
 # Source environment variables
  ENV_FILE="$(dirname "$0")/pg-backup.env"
  if [[ -f "$ENV_FILE" ]]; then
      source "$ENV_FILE"
      echo "Sourced environment variables from $ENV_FILE"
  fi

# Function to send Discord notification
send_discord_notification() {
    local message="$1"
    curl -X POST http://localhost:30008/alert \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\"}" \
        --silent --show-error
}

# Configurable Variables
DB_HOST="localhost"
DB_PORT="5432"
MY_DB_NAME="finance"
PARENTS_DB_NAME="parents_finance"
METABASE_DB_NAME="metabase"
DB_USER="${PG_BACKUP_USER}"
DB_PASSWORD="${PG_BACKUP_PASSWORD}"
BASE_BACKUP_DIR="/home/nathan/pg-backup"
BASE_REMOTE_DIR="/nathan/pg-backup"
FTP_HOST="195.168.1.14"
FTP_USER="${PG_BACKUP_FTP_USER}"
FTP_PASS="${PG_BACKUP_FTP_PASS}"
KEEP_DAYS=60  # Number of days to keep local backups

# List of databases to back up
DBS_TO_BACKUP=("$MY_DB_NAME" "$PARENTS_DB_NAME" "$METABASE_DB_NAME")

# Check if required environment variables are set
if [[ -z "$DB_USER" ]] || [[ -z "$DB_PASSWORD" ]]; then
    ERROR_MSG="❌ PostgreSQL Backup Failed: PG_BACKUP_USER and PG_BACKUP_PASSWORD environment variables must be set!"
    echo "$ERROR_MSG" >&2
    send_discord_notification "$ERROR_MSG"
    exit 1
fi

if [[ -z "$FTP_USER" ]] || [[ -z "$FTP_PASS" ]]; then
    ERROR_MSG="❌ PostgreSQL Backup Failed: PG_BACKUP_FTP_USER and PG_BACKUP_FTP_PASS environment variables must be set!"
    echo "$ERROR_MSG" >&2
    send_discord_notification "$ERROR_MSG"
    exit 1
fi

for DB_NAME in "${DBS_TO_BACKUP[@]}"; do
    echo "Backing up $DB_NAME"

    # Generate unique backup filename for this database
    BACKUP_FILE="backup_$(date +\%Y\%m\%d_%H%M%S).sql"

    # Ensure backup directory exists
    BACKUP_DIR="$BASE_BACKUP_DIR/$DB_NAME"
    mkdir -p "$BACKUP_DIR"

    # stream pg_dump directly to local file
    PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F p -b -v "$DB_NAME" > "$BACKUP_DIR/$BACKUP_FILE"

    # Check if pg_dump succeeded
    if [[ $? -ne 0 ]]; then
        ERROR_MSG="❌ PostgreSQL Backup Failed: pg_dump failed for database $DB_NAME"
        echo "$ERROR_MSG" >&2
        send_discord_notification "$ERROR_MSG"
        exit 1
    fi

    # Verify the backup file exists and is not empty
    if [[ ! -s "$BACKUP_DIR/$BACKUP_FILE" ]]; then
        ERROR_MSG="❌ PostgreSQL Backup Failed: Backup file is missing or empty for database $DB_NAME"
        echo "$ERROR_MSG" >&2
        send_discord_notification "$ERROR_MSG"
        exit 1
    fi

    # Upload backup file to FTP server
    REMOTE_DIR="$BASE_REMOTE_DIR/$DB_NAME"
    echo "Uploading $BACKUP_FILE to FTP server..."

    lftp ftp://"$FTP_HOST" \
    -u "$PG_BACKUP_FTP_USER,$PG_BACKUP_FTP_PASS" \
    -e "
        set ssl:verify-certificate no
        mkdir -p $REMOTE_DIR
        cd $REMOTE_DIR
        put $BACKUP_DIR/$BACKUP_FILE
        bye
    "

    # Check if upload was successful
    if [[ $? -eq 0 ]]; then
        LINE_COUNT=$(wc -l < "$BACKUP_DIR/$BACKUP_FILE")
        SUCCESS_MSG="✅ PostgreSQL Backup Success: $DB_NAME backed up to FTP ($BACKUP_FILE, $LINE_COUNT lines)"
        echo "$SUCCESS_MSG"
        send_discord_notification "$SUCCESS_MSG"
    else
        ERROR_MSG="❌ PostgreSQL Backup Failed: FTP upload failed for database $DB_NAME"
        echo "$ERROR_MSG" >&2
        send_discord_notification "$ERROR_MSG"
        exit 1
    fi

    # Find and delete old backups
    echo "Checking for old backups to delete..."
    OLD_BACKUPS=$(find "$BACKUP_DIR" -type f -name "backup_*.sql" -mtime +$KEEP_DAYS)

    if [[ -z "$OLD_BACKUPS" ]]; then
        echo "No old backups found to delete."
    else
        echo "$OLD_BACKUPS" | while read backup_path; do
            echo "Deleting $backup_path"
            backup_file=$(basename "$backup_path")

            # Delete from local storage
            echo "Deleting $backup_file locally..."
            rm "$backup_path"

            # Delete from FTP server
            echo "Deleting $backup_file from FTP server..."

            lftp ftp://"$FTP_HOST" \
            -u "$PG_BACKUP_FTP_USER,$PG_BACKUP_FTP_PASS" \
            -e "
                set ssl:verify-certificate no
                cd $REMOTE_DIR
                rm $backup_file
                bye
            "

            if [[ $? -eq 0 ]]; then
                echo "Successfully deleted $backup_file from FTP server."
            else
                echo "Warning: Failed to delete $backup_file from FTP server." >&2
            fi
        done
    fi
done

COMPLETION_MSG="✅ PostgreSQL Backup Complete: All databases backed up successfully"
echo "$COMPLETION_MSG"
send_discord_notification "$COMPLETION_MSG"
