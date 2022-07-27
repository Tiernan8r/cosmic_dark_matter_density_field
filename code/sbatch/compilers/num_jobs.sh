#!/usr/bin/bash

echo "Working from: ${PWD}"

COMMENT_REGEX="#([[:space:]])?.*"

FILTERED_REDSHIFTS=()
while read Z; do
    # Skip commented out entries
    if [[ "${Z}" =~ $COMMENT_REGEX ]]; then
        continue
    fi
    FILTERED_REDSHIFTS+=("${Z}")
done < ./sbatch/compilers/redshifts.txt

FILTERED_RADII=()
while read R; do
    # Skip commented out entries
    if [[ "${R}" =~ $COMMENT_REGEX ]]; then
        continue
    fi
    FILTERED_RADII+=("${R}")
done < ./sbatch/compilers/radii.txt

FILTERED_SIMULATIONS=()
while read S; do
    # Skip commented out entries
    if [[ "${S}" =~ $COMMENT_REGEX ]]; then
        continue
    fi
    FILTERED_SIMULATIONS+=("${S}")
done < ./sbatch/compilers/datasets.txt

NUM_REDSHIFTS=${#FILTERED_REDSHIFTS[@]}
NUM_RADII=${#FILTERED_RADII[@]}
NUM_SIMULATIONS=${#FILTERED_SIMULATIONS[@]}

echo "Have ${NUM_REDSHIFTS} redshifts"
echo "Have ${NUM_RADII} radii"
echo "Have ${NUM_SIMULATIONS} simulation datasets"

TOTAL=$(($NUM_REDSHIFTS*$NUM_RADII*$NUM_SIMULATIONS))

echo "So ${TOTAL} total compiled files (!)"
