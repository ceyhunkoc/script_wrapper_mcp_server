#!/bin/bash

# List files in directory with various options
# Usage: ./list_files.sh [directory] [options]

DIRECTORY=${1:-.}
OPTIONS=${2:-"-la"}

echo "Listing files in directory: $DIRECTORY"
echo "Options: $OPTIONS"
echo "----------------------------------------"

if [ ! -d "$DIRECTORY" ]; then
    echo "Error: Directory '$DIRECTORY' does not exist"
    exit 1
fi

ls $OPTIONS "$DIRECTORY"

echo "----------------------------------------"
echo "Total files: $(ls -1 "$DIRECTORY" | wc -l)"