#!/bin/bash

THREADS=4
CONFIG_FILE="chunker_config.json"

while getopts t:c: flag
do
    case "${flag}" in
        t) THREADS=${OPTARG};;
        c) CONFIG_FILE=${OPTARG};;
    esac
done

echo "Running chunker with $THREADS threads and configuration file $CONFIG_FILE"

python chunker/chunk_text.py --threads $THREADS --config $CONFIG_FILE