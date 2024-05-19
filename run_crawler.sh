#!/bin/bash

CONFIG="crawler_config.json"

while getopts ":c:" opt; do
  case $opt in
    c) CONFIG=$OPTARG ;;
    \?) echo "Invalid option -$OPTARG" >&2
        exit 1 ;;
  esac
done

cd scraper
python run_crawlers.py --config $CONFIG
