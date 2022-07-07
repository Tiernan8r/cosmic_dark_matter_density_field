#!/usr/env/bin bash

FILES=$(ls -d "$PWD/sbatch/spheres"/* | grep -E ".*spheres_r[[:digit:]]+_z[[:digit:]]+.sh$")

for F in $FILES; do
    echo "Batching '${F}'"
    sbatch ${F}
done
