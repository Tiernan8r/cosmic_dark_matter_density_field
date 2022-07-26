#!/usr/bin/bash

echo "Working from: ${PWD}"

NUM_REDSHIFTS=$(wc -w < ./sbatch/compilers/redshifts.txt)
NUM_RADII=$(wc -w < ./sbatch/compilers/radii.txt)
NUM_SIMULATIONS=$(wc -w < ./sbatch/compilers/datasets.txt)

echo "Have ${NUM_REDSHIFTS} redshifts"
echo "Have ${NUM_RADII} radii"
echo "Have ${NUM_SIMULATIONS} simulation datasets"

TOTAL=$(($NUM_REDSHIFTS*$NUM_RADII*$NUM_SIMULATIONS))

echo "So ${TOTAL} total compiled files (!)"
