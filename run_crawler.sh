#!/bin/bash

CONFIG="configs/crawler_config.json"

while getopts ":c:" opt; do
  case $opt in
    c) CONFIG=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2
        exit 1 ;;
  esac
done

python scraper/run_crawlers.py --config $CONFIG
