#! /usr/bin/bash

# FILE ASSUMES IT IS RUN FROM code/

RADII=$(cat ./sbatch/compilers/radii.txt)
REDSHIFTS=$(cat ./sbatch/compilers/redshifts.txt)

num_sp_samples=1000

for R in ${RADII[@]}; do
    for Z in ${REDSHIFTS[@]}; do
        # ============
        # CONFIG
        # ============
        job_name="r${R}_z${Z}"
        out_name="./configs/radii/${job_name}.yaml"

        config_file="configs/radii/${job_name}.yaml"
        cache="!include ../defaults/radii_cache.yaml"
        r="\n  - ${R}"
        z="\n  - ${Z}"
        sampling="\n  num_sp_samples: ${num_sp_samples}"

        ./sbatch/compilers/config.sh -r "${r}" -z "${z}" -c "${cache}" -s "${sampling}" "${config_file}" "${out_name}"
    done
done