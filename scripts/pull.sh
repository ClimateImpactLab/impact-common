#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Please provide a subdirectory."
    exit 1
fi

if [ -f synced ]; then
    # Make any parent directories
    mkdir -p $1

    # Copy the directory
    rsync -avz sacagawea.gspp.berkeley.edu:/shares/gcp/$1/ $1
else
    echo "Current directory doees not appear synced.  Please run setup.sh."
fi

