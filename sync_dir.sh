#!/bin/bash

SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" # Folder of current script
DEST_DIR="$( cd . && pwd )"

echo "Source dir: $SRC_DIR"
echo "Destination dir: $DEST_DIR"

# If SRC_DIR and DEST_DIR are the same, then show an error message and exit
if [ "$SRC_DIR" == "$DEST_DIR" ]; then
    echo "ERROR: Source and destination directories are the same. Run the script from Destination dir."
    exit 1
fi

rsync -av --exclude-from="$SRC_DIR/.gitignore" --exclude=".git" "$SRC_DIR/" "$DEST_DIR"
