#!/bin/bash
SOURCE_DIR="/RAID6"
DEST_USER="urseismoadmin"
DEST_HOST="10.17.7.230"
DEST_DIR="/volumeUSB1/usbshare/Archive/terravibranium_RAID6/"
DATE=$(date +"%Y-%m-%d %H:%M:%S")
SSH_CMD="ssh -i ~/.ssh/id_rsa_atos -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=240"

# Ensure destination exists
ssh -i ~/.ssh/id_rsa_atos -o StrictHostKeyChecking=no "$DEST_USER@$DEST_HOST" "mkdir -p '$DEST_DIR'"

# Change directory first, then find relative paths to avoid rsync double-prefixing
cd "$SOURCE_DIR" || exit 1
export DEST_USER DEST_HOST SSH_CMD
find . -type f -mtime +730 2>/dev/null -print0 | xargs -0 -n 5000 sh -c '
    DEST_VOL=$(ssh -i ~/.ssh/id_rsa_atos -o StrictHostKeyChecking=no "$DEST_USER@$DEST_HOST" "df -BG /volumeUSB*/usbshare | awk '\''NR>1 && \$4+0 > 500 {print \$6; exit}'\''")
    if [ -z "$DEST_VOL" ]; then echo "ALL USB DISKS FULL! Cannot sync."; exit 1; fi
    DEST_DIR="${DEST_VOL}/Archive/terravibranium_RAID6/"
    ssh -i ~/.ssh/id_rsa_atos -o StrictHostKeyChecking=no "$DEST_USER@$DEST_HOST" "mkdir -p '\''$DEST_DIR'\''"
    echo "Pushing batch of $# files to $DEST_DIR..."
    rsync -0 -avPR -e "$SSH_CMD" --remove-source-files "$@" "$DEST_USER@$DEST_HOST:$DEST_DIR"
' _

# Clean up empty directories left behind
find . -mindepth 1 -type d -empty 2>/dev/null -delete

# Drop a README file
echo "ARCHIVE NOTICE: Files older than 2 years from this directory were automatically moved to ATOS-nas (10.17.7.230) on $DATE to free up space (spanning /volumeUSB*/usbshare/Archive/terravibranium_RAID6/)." > README_ARCHIVED.txt 2>/dev/null
