#!/bin/bash

THREADS=4  

echo "Running embedder with $THREADS threads"

python embedder/embed_chunks.py --threads $THREADS