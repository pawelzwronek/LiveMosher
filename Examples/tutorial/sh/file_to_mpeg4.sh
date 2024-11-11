#!/bin/bash

# Check if a filename was passed as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

# Check if stdout is being piped
if [ -t 1 ]; then
    echo "Error: Output must be piped."
    exit 1
fi

# Run the command with the provided filename
./bin/ffgac -i "$1" -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -g max -sc_threshold max -f rawvideo pipe:
