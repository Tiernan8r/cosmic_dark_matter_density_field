#!/usr/bin/env bash

JOB_IDS=$(squeue --me -o %A)

for ID in ${JOB_IDS}; do
	echo "Cancelling job - ${ID}"
	scancel ${ID}
done

