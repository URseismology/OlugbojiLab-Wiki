#!/bin/bash

# Configuration
MASTER_DIR="/mnt/production_uploads/course_master_2026"
CLASS_DIR="/mnt/production_uploads/class_work"

TARGET=$1
STUDENT_FILTER=$2

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <target_folder> [specific_student]"
    echo "Example: $0 Lab_01"
    echo "Example: $0 data sswar"
    exit 1
fi

SOURCE_PATH="$MASTER_DIR/$TARGET"

if [ ! -d "$SOURCE_PATH" ]; then
    echo "Error: Target $SOURCE_PATH does not exist in the master directory."
    exit 1
fi

echo "============================================="
echo "🚀 Deploying $TARGET..."
if [ ! -z "$STUDENT_FILTER" ]; then
    echo "   (Restricted to student: $STUDENT_FILTER)"
fi
echo "============================================="

for student_dir in "$CLASS_DIR"/*; do
    if [ -d "$student_dir" ]; then
        student_name=$(basename "$student_dir")
        
        # Ensure we don't deploy into non-student directories
        if [[ "$student_name" == "pushlabs" ]]; then
            continue
        fi

        # If a filter is provided, skip other students
        if [ ! -z "$STUDENT_FILTER" ] && [ "$student_name" != "$STUDENT_FILTER" ]; then
            continue
        fi

        echo "Pushing to student: $student_name..."
        
        # Copy the specific folder into the student's directory
        cp -r -u "$SOURCE_PATH" "$student_dir/" 2>/dev/null
    fi
done

echo "============================================="
echo "✅ $TARGET deployed successfully!"
echo "============================================="
