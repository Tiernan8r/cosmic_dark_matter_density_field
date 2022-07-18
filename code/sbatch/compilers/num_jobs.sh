#!/usr/bin/bash

echo "Working from: ${PWD}"

RADII_CONTENT=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS_CONTENT=$(cat ./sbatch/compilers/redshifts.txt)
SIMULATIONS_CONTENT=$(cat ./sbatch/compilers/datasets.txt)

OLD_IFS="${IFS}"
IFS=" "

read -ra RADII <<< "${RADII_CONTENT}"
read -ra REDSHIFTS <<< "${REDSHIFTS_CONTENT}"
read -ra SIMULATIONS <<< "${SIMULATIONS_CONTENT}"

IFS="${OLD_IFS}"

NUM_REDSHIFTS=${#REDSHIFTS[@]}
NUM_RADII=${#RADII[@]}
NUM_SIMULATIONS=${#SIMULATIONS[@]}

echo "Have ${NUM_REDSHIFTS} redshifts"
echo "Have ${NUM_RADII} radii"
echo "Have ${NUM_SIMULATIONS} simulation datasets"

TOTAL=$(($NUM_REDSHIFTS*$NUM_RADII*$NUM_SIMULATIONS))

echo "So ${TOTAL} total compiled files (!)"
