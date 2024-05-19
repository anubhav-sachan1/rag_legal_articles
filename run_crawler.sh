#!/bin/bash

THREADS=4
CONFIG="crawler_config.json"

while getopts ":t:c:" opt; do
  case $opt in
    t) THREADS=$OPTARG ;;
    c) CONFIG=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2
        exit 1 ;;
  esac
done

python scraper/run_crawlers.py --threads $THREADS --config $CONFIG
