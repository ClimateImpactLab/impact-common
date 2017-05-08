#!/bin/bash

if [ -f synced ]; then
    rsync -avzu ./ sacagawea.gspp.berkeley.edu:/shares/gcp/
else
    echo "Current directory doees not appear synced.  Please run setup.sh.
fi
