#!/bin/bash
set -x
# This reverses the direction to bypass University Firewall drops

export SOURCE_USER="administrator"
export SOURCE_HOST="repovibranium.earth.rochester.edu"
export DEST_DIR="/volumeUSB1/usbshare/Archive/repovibranium_bluehive/"
export SSH_CMD="ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=240"

echo "Starting Pull Archival from repovibranium to ATOS-nas..."
mkdir -p "$DEST_DIR"

# Find all bluehive directories on repovibranium
$SSH_CMD -n "$SOURCE_USER@$SOURCE_HOST" 'find /volume1 /volume2 -maxdepth 4 -type d -iname "*bluehive*" 2>/dev/null' | while read BLUEHIVE_DIR; do
    echo "Processing $BLUEHIVE_DIR..."
    export BLUEHIVE_DIR
    
    # Generate list of files older than 730 days on repovibranium and stream to xargs on ATOS-nas
    # We use -print0 over SSH to safely handle filenames with spaces
    $SSH_CMD -n "$SOURCE_USER@$SOURCE_HOST" "cd '$BLUEHIVE_DIR' && find . -type f -mtime +730 2>/dev/null -print0" | xargs -0 -n 5000 sh -c '
        if [ "$#" -eq 0 ]; then exit 0; fi
        DEST_VOL=$(df -BG /volumeUSB*/usbshare | awk '\''NR>1 && $4+0 > 500 {print $6; exit}'\'')
        if [ -z "$DEST_VOL" ]; then echo "ALL USB DISKS FULL! Cannot sync."; exit 1; fi
        DEST_DIR="${DEST_VOL}/Archive/repovibranium_bluehive/"
        mkdir -p "$DEST_DIR"
        printf "%s\0" "$@" > /tmp/batch.list
        echo "Pulling batch of $# files to $DEST_DIR..."
        rsync -0 -avPR -e "$SSH_CMD" --remove-source-files --files-from=/tmp/batch.list "$SOURCE_USER@$SOURCE_HOST:$BLUEHIVE_DIR/" "$DEST_DIR"
    ' _
    
    echo "Cleaning up empty directories on repovibranium..."
    $SSH_CMD -n "$SOURCE_USER@$SOURCE_HOST" "cd '$BLUEHIVE_DIR' && find . -mindepth 1 -type d -empty 2>/dev/null -delete"
    
    echo "Leaving audit trail..."
    DATE=$(date +"%Y-%m-%d %H:%M:%S")
    $SSH_CMD -n "$SOURCE_USER@$SOURCE_HOST" "echo '"'ARCHIVE NOTICE: Files older than 2 years from this directory were automatically moved to ATOS-nas (10.17.7.230) via Pull at '"$DEST_DIR"' on '"$DATE"' to free up space.'" > '$BLUEHIVE_DIR/README_ARCHIVED.txt'"
done

echo "Pull Archival Complete!"
