#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Please specify a directory to hold the GCP data."
fi

DIR="$( dirname "${BASH_SOURCE[0]}" )"

mkdir $1
cp $DIR/push.sh $1
cp $DIR/pull.sh $1
cp $DIR/check.sh $1
touch $1/synced

