#!/usr/bin/env bash

FILES=$(ls -d "$PWD/sbatch/radii"/* | grep -E ".*r[[:digit:]\.]+_z[[:digit:]\.]+-.*\.sh$")

for F in $FILES; do
    echo "Batching '${F}'"
    sbatch ${F}
done
