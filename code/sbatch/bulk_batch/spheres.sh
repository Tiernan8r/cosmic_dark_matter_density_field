#!/usr/bin/env bash

echo "Searching from: ${PWD}"

FILES=$(ls -d "$PWD/sbatch/spheres"/* | grep -E ".*sp_r[[:digit:]\.]+_z[[:digit:]\.]+.sh$")

for F in $FILES; do
    echo "Batching '${F}'"
    sbatch ${F}
done
